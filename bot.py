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
        [InlineKeyboardButton("🔎 Buscar documento", callback_data="cmd_buscar")],
    ]
    with open(IMAGEN, "rb") as img:
        await update.message.reply_photo(
            photo=img,
            caption="👋 Bienvenido\n\n💻 Conéctate al conocimiento.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    archivos = os.listdir(CARPETA)
    total = len(archivos)
    if not archivos:
        await update.message.reply_text("😔 No hay libros disponibles por el momento.")
        return
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in archivos]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   📚 CATÁLOGO COMPLETO\n"
        f"╚═══════════════════════╝\n\n"
        f"📊 Total de libros: {total}\n\n"
        f"Selecciona un documento:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   🔎 BUSCADOR DE LIBROS\n"
            "╚═══════════════════════╝\n\n"
            "📚 ¿Qué libro estás buscando?\n\n"
            "✏️ Escribe en el chat:\n"
            "/buscar + el nombre del libro\n\n"
            "📖 Ejemplo:\n"
            "/buscar Tú Eres tu Prioridad\n\n"
            "💡 Tip: Puedes buscar por\n"
            "una palabra del título"
        )
        return
    palabra = " ".join(context.args).lower()
    archivos = os.listdir(CARPETA)
    resultados = [a for a in archivos if palabra in a.lower()]
    if not resultados:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   😔 SIN RESULTADOS\n"
            "╚═══════════════════════╝\n\n"
            "No encontramos ese libro.\n\n"
            "💡 Intenta con:\n"
            "• Una sola palabra del título\n"
            "• Verificar la ortografía\n\n"
            "📚 También puedes ver el\n"
            "catálogo completo con /lista"
        )
        return
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in resultados]
    await update.message.reply_text("🔎 Resultados:", reply_markup=InlineKeyboardMarkup(keyboard))

async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cmd_buscar":
        await query.message.reply_text(
            "╔═══════════════════════╗\n"
            "   🔎 BUSCADOR DE LIBROS\n"
            "╚═══════════════════════╝\n\n"
            "📚 ¿Qué libro estás buscando?\n\n"
            "✏️ Escribe en el chat:\n"
            "/buscar + el nombre del libro\n\n"
            "📖 Ejemplo:\n"
            "/buscar Tú Eres tu Prioridad\n\n"
            "💡 Tip: Puedes buscar por\n"
            "una palabra del título"
        )
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
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling()
