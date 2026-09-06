import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# 1. Servidor Web dummy para mantener activo el Web Service gratuito de Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Jarvis está activo y corriendo en segundo plano."

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 2. Cargar claves desde las Variables de Entorno de Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

# 3. Lógica del Bot de Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy Jarvis, tu asistente personal. ¿En qué te puedo ayudar hoy?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres Jarvis, un asistente personal inteligente, rápido, eficiente y conciso. Respondes en español de forma directa y atenta."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        
        response = chat_completion.choices[0].message.content
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"Ocurrió un error al procesar tu solicitud: {str(e)}")

# 4. Función Principal
def main():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Jarvis está activo y escuchando...")
    application.run_polling()

if __name__ == "__main__":
    main()
