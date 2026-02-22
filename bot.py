import os
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ.get('TOKEN')
CARPETA = "documentos"
IMAGEN = "bienvenida.png"

def iniciar_servidor():
    handler = http.server.BaseHTTPRequestHandler
    with socketserver.TCPServer(("", 10000), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=iniciar_servidor, daemon=True).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔎 Buscar documento", switch_inline_query_current_chat="/buscar ")],
        [InlineKeyboardButton("📂 Ver todos los documentos", callback_data="cmd_lista")],
        [InlineKeyboardButton("🗂️ Ver categorías", callback_data="cmd_cmds")],
    ]
    with open(IMAGEN, "rb") as img:
        await update.message.reply_photo(
            photo=img,
            caption="💻 Conéctate al conocimiento. Bienvenido.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("SUNAT 🏛️", callback_data="cat_SUNAT"),
            InlineKeyboardButton("CERTIFICADOS 📋", callback_data="cat_CERTIFICADOS"),
        ],
        [
            InlineKeyboardButton("ACTAS 📄", callback_data="cat_ACTAS"),
            InlineKeyboardButton("TELEFONIA 📱", callback_data="cat_TELEFONIA"),
        ],
        [
            InlineKeyboardButton("FAMILIARES 👨‍👩‍👧", callback_data="cat_FAMILIARES"),
            InlineKeyboardButton("MIGRACIONES 🌐", callback_data="cat_MIGRACIONES"),
        ],
    ]
    if update.message:
        await update.message.reply_text("🗂️ Selecciona una categoría:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("🗂️ Selecciona una categoría:", reply_markup=InlineKeyboardMarkup(keyboard))

async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    archivos = os.listdir(CARPETA)
    if not archivos:
        await update.message.reply_text("No hay documentos disponibles.")
        return
    keyboard = [[InlineKeyboardButton(archivo, callback_data=archivo)] for archivo in archivos]
    if update.message:
        await update.message.reply_text("📂 Selecciona un documento:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text("📂 Selecciona un documento:", reply_markup=InlineKeyboardMarkup(keyboard))

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /buscar palabra")
        return
    palabra = " ".join(context.args).lower()
    archivos = os.listdir(CARPETA)
    resultados = [a for a in archivos if palabra in a.lower()]
    if not resultados:
        await update.message.reply_text("No se encontraron archivos.")
        return
    keyboard = [[InlineKeyboardButton(a, callback_data=a)] for a in resultados]
    await update.message.reply_text("🔎 Resultados:", reply_markup=InlineKeyboardMarkup(keyboard))

async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cmd_lista":
        archivos = os.listdir(CARPETA)
        if not archivos:
            await query.message.reply_text("No hay documentos disponibles.")
            return
        keyboard = [[InlineKeyboardButton(a, callback_data=a)] for a in archivos]
        await query.message.reply_text("📂 Selecciona un documento:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cmd_cmds":
        await cmds(update, context)
        return

    if query.data.startswith("cat_"):
        categoria = query.data.replace("cat_", "").lower()
        archivos = os.listdir(CARPETA)
        resultados = [a for a in archivos if categoria in a.lower()]
        if not resultados:
            await query.message.reply_text("No hay archivos en esta categoría.")
            return
        keyboard = [[InlineKeyboardButton(a, callback_data=a)] for a in resultados]
        await query.message.reply_text(f"📂 Archivos de {categoria.upper()}:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    ruta = os.path.join(CARPETA, query.data)
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            await query.message.reply_document(f)
    else:
        await query.message.reply_text("Archivo no encontrado.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lista", lista))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CommandHandler("cmds", cmds))
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling()