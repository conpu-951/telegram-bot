import os
import json
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.environ.get('TOKEN')
CARPETA = "documentos"
IMAGEN = "bienvenida.png"
FAVORITOS_FILE = "favoritos.json"

def cargar_favoritos():
    if os.path.exists(FAVORITOS_FILE):
        with open(FAVORITOS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_favoritos(favoritos):
    with open(FAVORITOS_FILE, "w") as f:
        json.dump(favoritos, f)

def iniciar_servidor():
    handler = http.server.BaseHTTPRequestHandler
    with socketserver.TCPServer(("", 10000), handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=iniciar_servidor, daemon=True).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.set_my_commands([
        BotCommand("start", "🏠 Inicio"),
        BotCommand("lista", "📚 Ver catálogo completo"),
        BotCommand("buscar", "🔎 Buscar un libro"),
        BotCommand("favoritos", "⭐ Mis favoritos"),
    ])
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
        f"   📚 CATALOGO COMPLETO\n"
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
            "📚 Que libro estas buscando?\n\n"
            "✏️ Escribe en el chat:\n"
            "/buscar + el nombre del libro\n\n"
            "📖 Ejemplo:\n"
            "/buscar Tu Eres tu Prioridad\n\n"
            "💡 Tip: Puedes buscar por\n"
            "una palabra del titulo"
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
            "Una sola palabra del titulo\n"
            "Verificar la ortografia\n\n"
            "📚 Tambien puedes ver el\n"
            "catalogo completo con /lista"
        )
        return
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in resultados]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   ✅ LIBRO ENCONTRADO 🧐\n"
        f"╚═══════════════════════╝\n\n"
        f"📚 Se encontraron {len(resultados)} resultado(s)\n\n"
        f"👇 Presiona para descargar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def favoritos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    favs = cargar_favoritos()
    user_favs = favs.get(user_id, [])
    if not user_favs:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   ⭐ MIS FAVORITOS\n"
            "╚═══════════════════════╝\n\n"
            "😔 No tienes favoritos guardados.\n\n"
            "Descarga un libro y guárdalo\n"
            "en favoritos."
        )
        return
    keyboard = [
        [
            InlineKeyboardButton(f"📖 {a}", callback_data=a),
            InlineKeyboardButton("❌", callback_data=f"delfav_{user_id}_{a}")
        ]
        for a in user_favs
    ]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   ⭐ MIS FAVORITOS\n"
        f"╚═══════════════════════╝\n\n"
        f"📚 Tienes {len(user_favs)} favorito(s)\n\n"
        f"Presiona ❌ para eliminar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "cmd_buscar":
        await query.message.reply_text(
            "╔═══════════════════════╗\n"
            "   🔎 BUSCADOR DE LIBROS\n"
            "╚═══════════════════════╝\n\n"
            "📚 Que libro estas buscando?\n\n"
            "✏️ Escribe en el chat:\n"
            "/buscar + el nombre del libro\n\n"
            "📖 Ejemplo:\n"
            "/buscar Tu Eres tu Prioridad\n\n"
            "💡 Tip: Puedes buscar por\n"
            "una palabra del titulo"
        )
        return

    if query.data.startswith("delfav_"):
        partes = query.data.split("_", 2)
        archivo = partes[2]
        favs = cargar_favoritos()
        if user_id in favs and archivo in favs[user_id]:
            favs[user_id].remove(archivo)
            guardar_favoritos(favs)
            await query.message.reply_text(f"❌ {archivo} eliminado de favoritos.")
        return

    if query.data.startswith("addfav_"):
        archivo = query.data.replace("addfav_", "")
        favs = cargar_favoritos()
        if user_id not in favs:
            favs[user_id] = []
        if archivo not in favs[user_id]:
            favs[user_id].append(archivo)
            guardar_favoritos(favs)
            await query.message.reply_text(f"⭐ {archivo} guardado en favoritos.")
        else:
            await query.message.reply_text("Ya está en tus favoritos.")
        return

    ruta = os.path.join(CARPETA, query.data)
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            await query.message.reply_document(f)
        keyboard = [[InlineKeyboardButton("⭐ Guardar en favoritos", callback_data=f"addfav_{query.data}")]]
        await query.message.reply_text(
            "¿Te gustó este libro?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text("Archivo no encontrado.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lista", lista))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CommandHandler("favoritos", favoritos))
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling()
