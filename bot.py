print("wazzaa")

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ.get('8532999070:AAH3pbTvm2NlmU75S61eUEETAq4eKGSDVbM')
CARPETA = "documentos"

# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hola 👋\n\n"
        "Usa:\n"
        "/lista → Ver todos los documentos\n"
        "/buscar palabra → Buscar un documento"
    )

# -------- LISTA COMPLETA -------- 
async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    archivos = os.listdir(CARPETA)

    if not archivos:
        await update.message.reply_text("No hay documentos disponibles.")
        return

    keyboard = [
        [InlineKeyboardButton(archivo, callback_data=archivo)]
        for archivo in archivos
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📂 Selecciona un documento:",
        reply_markup=reply_markup
    )

# -------- BUSCADOR --------
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Entró al buscador")
    print("Argumentos:", context.args)

    if not context.args:
        await update.message.reply_text("Usa: /buscar palabra")
        return

    palabra = " ".join(context.args).lower()
    archivos = os.listdir(CARPETA)

    resultados = [
        archivo for archivo in archivos if palabra in archivo.lower()
    ]

    if not resultados:
        await update.message.reply_text("No se encontraron archivos.")
        return

    keyboard = [
        [InlineKeyboardButton(archivo, callback_data=archivo)]
        for archivo in resultados
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔎 Resultados encontrados:",
        reply_markup=reply_markup
    )

# -------- BOTONES --------
async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    archivo = query.data
    ruta = os.path.join(CARPETA, archivo)

    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            await query.message.reply_document(f)
    else:
        await query.message.reply_text("Archivo no encontrado.")

# -------- APP --------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lista", lista))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CallbackQueryHandler(boton))

print("Bot funcionando...")
app.run_polling()

