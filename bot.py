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
STATS_FILE = "estadisticas.json"

def cargar_favoritos():
    if os.path.exists(FAVORITOS_FILE):
        with open(FAVORITOS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_favoritos(favoritos):
    with open(FAVORITOS_FILE, "w") as f:
        json.dump(favoritos, f)

def cargar_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def registrar_descarga(archivo):
    stats = cargar_stats()
    stats[archivo] = stats.get(archivo, 0) + 1
    guardar_stats(stats)

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
        BotCommand("estadisticas", "📊 Estadísticas"),
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

async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = cargar_stats()
    if not stats:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   📊 ESTADISTICAS\n"
            "╚═══════════════════════╝\n\n"
            "😔 Aún no hay descargas\n"
            "registradas."
        )
        return
    ordenados = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    total_descargas = sum(stats.values())
    texto = (
        "╔═══════════════════════╗\n"
        "   📊 ESTADISTICAS\n"
        "╚═══════════════════════╝\n\n"
        f"📥 Total descargas: {total_descargas}\n\n"
        "🏆 Más descargados:\n\n"
    )
    medallas = ["🥇", "🥈", "🥉"]
    for i, (archivo, count) in enumerate(ordenados[:10]):
        medalla = medallas[i] if i < 3 else "📖"
        texto += f"{medalla} {archivo}\n    {count} descarga(s)\n\n"
    await update.message.reply_text(texto)

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
        registrar_descarga(query.data)
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
app.add_handler(CommandHandler("estadisticas", estadisticas))
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling(drop_pending_updates=True) 