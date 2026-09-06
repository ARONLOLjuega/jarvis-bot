import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from groq import Groq

# Servidor web dummy para Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Jarvis está activo y escuchando...", 200

# Configuración de variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
LAPTOP_IP = os.environ.get("LAPTOP_TAILSCALE_IP", "aron.tail030744.ts.net")
AGENT_TOKEN = os.environ.get("AGENT_SECRET_TOKEN", "mi_jarvis_secreto_2026")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- COMANDOS DEL BOT ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy Jarvis. Estoy listo para ayudarte. Usa /laptop_status para ver el estado de tu portátil.")

async def laptop_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pide los datos al agente local"""
    await update.message.reply_text("📡 Conectando con el portátil...")
    
    if "ts.net" in LAPTOP_IP:
        url = f"https://{LAPTOP_IP}/status"
    else:
        url = f"http://{LAPTOP_IP}:5000/status"
        
    headers = {"X-Agent-Token": AGENT_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            msg = (
                f"💻 **Estado del Portátil**\n\n"
                f"🧠 **CPU:** {data.get('cpu_usage', 'N/A')}%\n"
                f"📊 **RAM:** {data.get('ram_usage', 'N/A')}%\n"
                f"🔋 **Batería:** {data.get('battery_percent', 'N/A')}% "
                f"({'Cargando' if data.get('power_plugged') else 'Desenchufado'})"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif response.status_code == 401:
            await update.message.reply_text("❌ Error: No autorizado. Verifica la clave AGENT_SECRET_TOKEN.")
        else:
            await update.message.reply_text(f"⚠️ El agente respondió con código de error: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"🔴 No se pudo conectar con el portátil.\nError: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not groq_client:
        await update.message.reply_text("Groq no está configurado.")
        return
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_text}],
            temperature=0.7
        )
        await update.message.reply_text(completion.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Error con la IA: {e}")

def main():
    if not TELEGRAM_TOKEN:
        print("ERROR: No se encontró TELEGRAM_BOT_TOKEN")
        return

    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CommandHandler("laptop_status", laptop_status_command))
    tg_app.add_handler(CommandHandler("laptop", laptop_status_command))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False), daemon=True).start()
    
    tg_app.run_polling()

if __name__ == "__main__":
    main()
