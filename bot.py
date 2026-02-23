import os
import json
import random
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get('TOKEN')
CARPETA = "documentos"
IMAGEN = "bienvenida.png"
FAVORITOS_FILE = "favoritos.json"
STATS_FILE = "estadisticas.json"
PORTADAS = "portadas"
USUARIOS_FILE = "usuarios.json"
HISTORIAL_FILE = "historial.json"
RESEÑAS_FILE = "reseñas.json"
BLOQUEADOS_FILE = "bloqueados.json"
PENDIENTES = "pendientes"
ADMIN_ID = 6262593562

def cargar_json(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return json.load(f)
    return {}

def guardar_json(archivo, data):
    with open(archivo, "w") as f:
        json.dump(data, f)

def cargar_favoritos(): return cargar_json(FAVORITOS_FILE)
def guardar_favoritos(d): guardar_json(FAVORITOS_FILE, d)
def cargar_stats(): return cargar_json(STATS_FILE)
def guardar_stats(d): guardar_json(STATS_FILE, d)
def cargar_usuarios(): return cargar_json(USUARIOS_FILE)
def guardar_usuarios(d): guardar_json(USUARIOS_FILE, d)
def cargar_historial(): return cargar_json(HISTORIAL_FILE)
def guardar_historial(d): guardar_json(HISTORIAL_FILE, d)
def cargar_reseñas(): return cargar_json(RESEÑAS_FILE)
def guardar_reseñas(d): guardar_json(RESEÑAS_FILE, d)
def cargar_bloqueados(): return cargar_json(BLOQUEADOS_FILE)
def guardar_bloqueados(d): guardar_json(BLOQUEADOS_FILE, d)

def registrar_descarga(archivo):
    stats = cargar_stats()
    stats[archivo] = stats.get(archivo, 0) + 1
    guardar_stats(stats)

def registrar_usuario(user):
    usuarios = cargar_usuarios()
    uid = str(user.id)
    if uid not in usuarios:
        usuarios[uid] = {
            "nombre": user.full_name,
            "username": user.username or "sin username"
        }
        guardar_usuarios(usuarios)

def registrar_historial(user_id, archivo):
    historial = cargar_historial()
    uid = str(user_id)
    if uid not in historial:
        historial[uid] = []
    if archivo in historial[uid]:
        historial[uid].remove(archivo)
    historial[uid].insert(0, archivo)
    historial[uid] = historial[uid][:10]
    guardar_historial(historial)

def esta_bloqueado(user_id):
    bloqueados = cargar_bloqueados()
    return str(user_id) in bloqueados

def obtener_portada(nombre_archivo):
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    for ext in [".jpg", ".png"]:
        ruta = os.path.join(PORTADAS, f"{nombre_sin_ext}{ext}")
        if os.path.exists(ruta):
            return ruta
    return None

def obtener_todos_archivos():
    archivos = []
    for item in os.listdir(CARPETA):
        ruta = os.path.join(CARPETA, item)
        if os.path.isfile(ruta):
            archivos.append(item)
        elif os.path.isdir(ruta):
            for archivo in os.listdir(ruta):
                archivos.append(f"{item}/{archivo}")
    return archivos

def iniciar_servidor():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot funcionando")
        def log_message(self, format, *args):
            pass
    with socketserver.TCPServer(("", 10000), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=iniciar_servidor, daemon=True).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    await context.bot.set_my_commands([
        BotCommand("start", "🏠 Inicio"),
        BotCommand("catalogo", "📚 Ver catálogo completo"),
        BotCommand("top", "🏆 Top 10 más descargados"),
        BotCommand("categorias", "📂 Navegar por categorías"),
        BotCommand("buscar", "🔎 Buscar un libro"),
        BotCommand("aleatorio", "🔀 Libro al azar"),
        BotCommand("historial", "🕐 Mis últimas descargas"),
        BotCommand("favoritos", "⭐ Mis favoritos"),
        BotCommand("ayuda", "ℹ️ Cómo usar el bot"),
    ])
    keyboard = [
        [InlineKeyboardButton("📚 Catálogo", callback_data="cmd_catalogo"),
         InlineKeyboardButton("🏆 Top 10", callback_data="cmd_top")],
        [InlineKeyboardButton("📂 Categorías", callback_data="cmd_categorias"),
         InlineKeyboardButton("🔎 Buscar", callback_data="cmd_buscar")],
        [InlineKeyboardButton("🔀 Aleatorio", callback_data="cmd_aleatorio"),
         InlineKeyboardButton("ℹ️ Ayuda", callback_data="cmd_ayuda")],
    ]
    with open(IMAGEN, "rb") as img:
        await update.message.reply_photo(
            photo=img,
            caption="👋 Bienvenido\n\n💻 Conéctate al conocimiento.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    texto = (
        "╔═══════════════════════╗\n"
        "   ℹ️ GUÍA DE USO\n"
        "╚═══════════════════════╝\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📚 BUSCAR LIBROS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/catalogo → Ver todos los libros\n"
        "/top → Top 10 más descargados\n"
        "/categorias → Navegar por temas\n"
        "/buscar palabra → Buscar libro\n"
        "/aleatorio → Libro sorpresa\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⭐ TUS LIBROS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/favoritos → Tus libros guardados\n"
        "/historial → Últimas descargas\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📤 SUBIR LIBROS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Envía cualquier PDF al bot\n"
        "y será revisado por el admin.\n"
        "Si es aprobado, aparecerá en\n"
        "el catálogo para todos.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✍️ RESEÑAS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Cuando buscas un libro puedes:\n"
        "• Ver reseñas de otros usuarios\n"
        "• Dejar tu propia reseña (1-5⭐)\n\n"
        "💡 Tip: Puedes guardar libros\n"
        "en favoritos para acceder\n"
        "rápidamente después!"
    )
    await update.message.reply_text(texto)

async def catalogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    archivos = obtener_todos_archivos()
    total = len(archivos)
    if not archivos:
        await update.message.reply_text("😔 No hay libros disponibles.")
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

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    stats = cargar_stats()
    if not stats:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   🏆 TOP 10\n"
            "╚═══════════════════════╝\n\n"
            "😔 Aún no hay descargas registradas."
        )
        return
    ordenados = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a, _ in ordenados]
    medallas = ["🥇", "🥈", "🥉"]
    texto = (
        "╔═══════════════════════╗\n"
        "   🏆 TOP 10 LIBROS\n"
        "╚═══════════════════════╝\n\n"
    )
    for i, (archivo, count) in enumerate(ordenados):
        medalla = medallas[i] if i < 3 else f"{i+1}️⃣"
        texto += f"{medalla} {archivo}\n    📥 {count} descarga(s)\n\n"
    await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard))

async def categorias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    cats = [f for f in os.listdir(CARPETA) if os.path.isdir(os.path.join(CARPETA, f))]
    if not cats:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   📂 CATEGORIAS\n"
            "╚═══════════════════════╝\n\n"
            "😔 No hay categorías creadas aún."
        )
        return
    keyboard = [[InlineKeyboardButton(f"📁 {c}", callback_data=f"cat_{c}")] for c in cats]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   📂 CATEGORIAS\n"
        f"╚═══════════════════════╝\n\n"
        f"📁 Total: {len(cats)}\n\n"
        f"Selecciona una categoría:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
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
    archivos = [a for a in obtener_todos_archivos() if palabra in a.lower()]
    if not archivos:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   😔 SIN RESULTADOS\n"
            "╚═══════════════════════╝\n\n"
            "No encontramos ese libro.\n\n"
            "💡 Intenta con una sola\n"
            "palabra del titulo"
        )
        return
    for archivo in archivos:
        nombre_sin_ext = os.path.splitext(os.path.basename(archivo))[0]
        reseñas = cargar_reseñas()
        res_libro = reseñas.get(archivo, [])
        promedio = sum(r["puntuacion"] for r in res_libro) / len(res_libro) if res_libro else 0
        estrellas = "⭐" * int(promedio) if promedio > 0 else "Sin reseñas aún"
        portada = obtener_portada(os.path.basename(archivo))
        keyboard = [
            [InlineKeyboardButton("📥 Descargar", callback_data=archivo)],
            [InlineKeyboardButton("✍️ Ver reseñas", callback_data=f"verreseña_{archivo}"),
             InlineKeyboardButton("⭐ Dejar reseña", callback_data=f"reseña_{archivo}")]
        ]
        caption = f"📖 {nombre_sin_ext}\n\n{estrellas}\n{len(res_libro)} reseña(s)"
        if portada:
            with open(portada, "rb") as img:
                await update.message.reply_photo(
                    photo=img,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await update.message.reply_text(
                caption,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

async def aleatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    archivos = obtener_todos_archivos()
    if not archivos:
        await update.message.reply_text("😔 No hay libros disponibles.")
        return
    archivo = random.choice(archivos)
    nombre_sin_ext = os.path.splitext(os.path.basename(archivo))[0]
    portada = obtener_portada(os.path.basename(archivo))
    keyboard = [[InlineKeyboardButton("📥 Descargar", callback_data=archivo)]]
    caption = f"🔀 Libro aleatorio:\n\n📖 {nombre_sin_ext}"
    if portada:
        with open(portada, "rb") as img:
            await update.message.reply_photo(photo=img, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    uid = str(update.message.from_user.id)
    hist = cargar_historial()
    user_hist = hist.get(uid, [])
    if not user_hist:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   🕐 MI HISTORIAL\n"
            "╚═══════════════════════╝\n\n"
            "😔 No has descargado ningún libro aún."
        )
        return
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in user_hist]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   🕐 MI HISTORIAL\n"
        f"╚═══════════════════════╝\n\n"
        f"📚 Últimas {len(user_hist)} descargas:\n\n"
        f"Presiona para descargar de nuevo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def favoritos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    user_id = str(update.message.from_user.id)
    favs = cargar_favoritos()
    user_favs = favs.get(user_id, [])
    if not user_favs:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   ⭐ MIS FAVORITOS\n"
            "╚═══════════════════════╝\n\n"
            "😔 No tienes favoritos guardados."
        )
        return
    keyboard = [
        [InlineKeyboardButton(f"📖 {a}", callback_data=a),
         InlineKeyboardButton("❌", callback_data=f"delfav_{user_id}_{a}")]
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
    if esta_bloqueado(update.message.from_user.id):
        return
    registrar_usuario(update.message.from_user)
    stats = cargar_stats()
    usuarios = cargar_usuarios()
    if not stats:
        await update.message.reply_text(
            "╔═══════════════════════╗\n"
            "   📊 ESTADISTICAS\n"
            "╚═══════════════════════╝\n\n"
            "😔 Aún no hay descargas registradas."
        )
        return
    ordenados = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    total_descargas = sum(stats.values())
    texto = (
        "╔═══════════════════════╗\n"
        "   📊 ESTADISTICAS\n"
        "╚═══════════════════════╝\n\n"
        f"📥 Total descargas: {total_descargas}\n"
        f"👥 Total usuarios: {len(usuarios)}\n\n"
        "🏆 Más descargados:\n\n"
    )
    medallas = ["🥇", "🥈", "🥉"]
    for i, (archivo, count) in enumerate(ordenados[:10]):
        medalla = medallas[i] if i < 3 else "📖"
        texto += f"{medalla} {archivo}\n    {count} descarga(s)\n\n"
    await update.message.reply_text(texto)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    usuarios = cargar_usuarios()
    bloqueados = cargar_bloqueados()
    categorias_list = [f for f in os.listdir(CARPETA) if os.path.isdir(os.path.join(CARPETA, f))]
    libros = [f for f in os.listdir(CARPETA) if os.path.isfile(os.path.join(CARPETA, f))]
    pendientes = os.listdir(PENDIENTES) if os.path.exists(PENDIENTES) else []
    await update.message.reply_text(
        "╔═══════════════════════╗\n"
        "   👤 PANEL DE ADMIN\n"
        "╚═══════════════════════╝\n\n"
        f"👥 Usuarios: {len(usuarios)}\n"
        f"🚫 Bloqueados: {len(bloqueados)}\n"
        f"📁 Categorias: {len(categorias_list)}\n"
        f"📚 Libros: {len(libros)}\n"
        f"⏳ Pendientes: {len(pendientes)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📤 AGREGAR LIBRO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Envía cualquier PDF al bot\n"
        "y se agregará automáticamente\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🖼️ AGREGAR PORTADA\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Envía una imagen con caption:\n"
        "nombre del libro.pdf\n"
        "Ej: casa.pdf\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🗑️ ELIMINAR LIBRO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/eliminar nombre.pdf\n"
        "Ej: /eliminar casa.pdf\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✏️ RENOMBRAR LIBRO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/renombrar actual.pdf nuevo.pdf\n"
        "Ej: /renombrar libro1.pdf nuevo.pdf\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📁 CREAR CATEGORIA\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/crearcategoria nombre\n"
        "Ej: /crearcategoria Motivacion\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📂 MOVER LIBRO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/mover libro.pdf Categoria\n"
        "Ej: /mover casa.pdf Motivacion\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚫 BLOQUEAR USUARIO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/bloquear ID\n"
        "Ej: /bloquear 123456789\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ DESBLOQUEAR USUARIO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/desbloquear ID\n"
        "Ej: /desbloquear 123456789\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📈 REPORTE SEMANAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/reporte\n"
        "Ver resumen de actividad\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📢 BROADCAST\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/broadcast mensaje\n"
        "Ej: /broadcast Nuevo libro!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 VER USUARIOS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/usuarios\n"
        "Lista de todos los usuarios\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 ESTADISTICAS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/estadisticas\n"
        "Ver descargas por libro"
    )

async def bloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("✏️ Uso: /bloquear ID\n\nEjemplo:\n/bloquear 123456789")
        return
    uid = context.args[0]
    bloqueados = cargar_bloqueados()
    bloqueados[uid] = True
    guardar_bloqueados(bloqueados)
    await update.message.reply_text(f"🚫 Usuario {uid} bloqueado.")

async def desbloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("✏️ Uso: /desbloquear ID\n\nEjemplo:\n/desbloquear 123456789")
        return
    uid = context.args[0]
    bloqueados = cargar_bloqueados()
    if uid in bloqueados:
        del bloqueados[uid]
        guardar_bloqueados(bloqueados)
        await update.message.reply_text(f"✅ Usuario {uid} desbloqueado.")
    else:
        await update.message.reply_text(f"😔 El usuario {uid} no está bloqueado.")

async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    stats = cargar_stats()
    usuarios = cargar_usuarios()
    bloqueados = cargar_bloqueados()
    archivos = obtener_todos_archivos()
    total_descargas = sum(stats.values()) if stats else 0
    top3 = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:3] if stats else []
    texto = (
        "╔═══════════════════════╗\n"
        "   📈 REPORTE DE ACTIVIDAD\n"
        "╚═══════════════════════╝\n\n"
        f"👥 Total usuarios: {len(usuarios)}\n"
        f"🚫 Usuarios bloqueados: {len(bloqueados)}\n"
        f"📚 Total libros: {len(archivos)}\n"
        f"📥 Total descargas: {total_descargas}\n\n"
        "🏆 Top 3 más descargados:\n\n"
    )
    medallas = ["🥇", "🥈", "🥉"]
    for i, (archivo, count) in enumerate(top3):
        texto += f"{medallas[i]} {archivo}\n    {count} descarga(s)\n\n"
    await update.message.reply_text(texto)

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("✏️ Uso: /eliminar nombre.pdf")
        return
    nombre = " ".join(context.args)
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
        await update.message.reply_text(f"✅ {nombre} eliminado.")
    else:
        await update.message.reply_text(f"😔 No se encontró {nombre}.")

async def renombrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("✏️ Uso: /renombrar actual.pdf nuevo.pdf")
        return
    actual, nuevo = context.args[0], context.args[1]
    ruta_actual = os.path.join(CARPETA, actual)
    ruta_nueva = os.path.join(CARPETA, nuevo)
    if os.path.exists(ruta_actual):
        os.rename(ruta_actual, ruta_nueva)
        await update.message.reply_text(f"✅ {actual} → {nuevo}")
    else:
        await update.message.reply_text(f"😔 No se encontró {actual}.")

async def crear_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("✏️ Uso: /crearcategoria nombre")
        return
    nombre = " ".join(context.args)
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        await update.message.reply_text(f"😔 La categoría {nombre} ya existe.")
    else:
        os.makedirs(ruta)
        await update.message.reply_text(f"✅ Categoría {nombre} creada.")

async def mover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("✏️ Uso: /mover libro.pdf Categoria")
        return
    libro, categoria = context.args[0], context.args[1]
    ruta_origen = os.path.join(CARPETA, libro)
    ruta_destino = os.path.join(CARPETA, categoria, libro)
    if not os.path.exists(ruta_origen):
        await update.message.reply_text(f"😔 No se encontró {libro}.")
        return
    if not os.path.exists(os.path.join(CARPETA, categoria)):
        await update.message.reply_text(f"😔 Categoría {categoria} no existe.\nCrea con /crearcategoria {categoria}")
        return
    os.rename(ruta_origen, ruta_destino)
    await update.message.reply_text(f"✅ {libro} movido a {categoria}.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("✏️ Uso: /broadcast mensaje")
        return
    mensaje = " ".join(context.args)
    usuarios = cargar_usuarios()
    enviados = fallidos = 0
    for uid in usuarios:
        try:
            await context.bot.send_message(int(uid), f"📢 Mensaje del administrador:\n\n{mensaje}")
            enviados += 1
        except:
            fallidos += 1
    await update.message.reply_text(f"✅ Enviados: {enviados}\n❌ Fallidos: {fallidos}")

async def ver_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    usuarios = cargar_usuarios()
    if not usuarios:
        await update.message.reply_text("😔 No hay usuarios aún.")
        return
    texto = f"╔═══════════════════════╗\n   📋 USUARIOS\n╚═══════════════════════╝\n\n👥 Total: {len(usuarios)}\n\n"
    for uid, datos in list(usuarios.items())[:20]:
        texto += f"👤 {datos['nombre']}\n   @{datos['username']}\n   ID: {uid}\n\n"
    await update.message.reply_text(texto)

async def recibir_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if esta_bloqueado(user_id):
        return
    doc = update.message.document
    if not doc.file_name.endswith(".pdf"):
        return
    if user_id == ADMIN_ID:
        archivo = await doc.get_file()
        ruta = os.path.join(CARPETA, doc.file_name)
        await archivo.download_to_drive(ruta)
        await update.message.reply_text(f"✅ {doc.file_name} agregado correctamente.")
        usuarios = cargar_usuarios()
        nombre_sin_ext = os.path.splitext(doc.file_name)[0]
        for uid in usuarios:
            try:
                await context.bot.send_message(int(uid), f"🔔 Nuevo libro disponible!\n\n📖 {nombre_sin_ext}\n\nEscribe /catalogo para verlo.")
            except:
                pass
    else:
        if not os.path.exists(PENDIENTES):
            os.makedirs(PENDIENTES)
        archivo = await doc.get_file()
        ruta = os.path.join(PENDIENTES, f"{user_id}_{doc.file_name}")
        await archivo.download_to_drive(ruta)
        await update.message.reply_text("📤 Tu libro fue enviado para revisión.\nEl administrador lo revisará pronto.")
        keyboard = [
            [InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{user_id}_{doc.file_name}"),
             InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{user_id}_{doc.file_name}")]
        ]
        await context.bot.send_message(
            ADMIN_ID,
            f"📬 Nuevo libro pendiente:\n\n📖 {doc.file_name}\n👤 Usuario ID: {user_id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def recibir_portada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not update.message.caption:
        await update.message.reply_text("⚠️ Envía la imagen con el nombre del libro como caption.\nEj: casa.pdf")
        return
    nombre_libro = update.message.caption.strip()
    nombre_sin_ext = os.path.splitext(nombre_libro)[0]
    if not os.path.exists(PORTADAS):
        os.makedirs(PORTADAS)
    foto = update.message.photo[-1]
    archivo = await foto.get_file()
    ruta = os.path.join(PORTADAS, f"{nombre_sin_ext}.jpg")
    await archivo.download_to_drive(ruta)
    await update.message.reply_text(f"✅ Portada de {nombre_sin_ext} guardada.")

async def boton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if query.data == "cmd_catalogo":
        archivos = obtener_todos_archivos()
        keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in archivos]
        await query.message.reply_text("📚 Catálogo completo:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cmd_top":
        stats = cargar_stats()
        if not stats:
            await query.message.reply_text("😔 Aún no hay descargas.")
            return
        ordenados = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
        keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a, _ in ordenados]
        await query.message.reply_text("🏆 Top 10:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cmd_categorias":
        cats = [f for f in os.listdir(CARPETA) if os.path.isdir(os.path.join(CARPETA, f))]
        if not cats:
            await query.message.reply_text("😔 No hay categorías aún.")
            return
        keyboard = [[InlineKeyboardButton(f"📁 {c}", callback_data=f"cat_{c}")] for c in cats]
        await query.message.reply_text("📂 Categorías:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cmd_buscar":
        await query.message.reply_text("🔎 Escribe:\n/buscar + nombre del libro\n\nEj: /buscar casa")
        return

    if query.data == "cmd_aleatorio":
        archivos = obtener_todos_archivos()
        if not archivos:
            await query.message.reply_text("😔 No hay libros.")
            return
        archivo = random.choice(archivos)
        nombre_sin_ext = os.path.splitext(os.path.basename(archivo))[0]
        keyboard = [[InlineKeyboardButton("📥 Descargar", callback_data=archivo)]]
        await query.message.reply_text(f"🔀 Libro aleatorio:\n\n📖 {nombre_sin_ext}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "cmd_ayuda":
        texto = (
            "╔═══════════════════════╗\n"
            "   ℹ️ GUÍA DE USO\n"
            "╚═══════════════════════╝\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📚 BUSCAR LIBROS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "/catalogo → Ver todos los libros\n"
            "/top → Top 10 más descargados\n"
            "/categorias → Navegar por temas\n"
            "/buscar palabra → Buscar libro\n"
            "/aleatorio → Libro sorpresa\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⭐ TUS LIBROS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "/favoritos → Tus libros guardados\n"
            "/historial → Últimas descargas\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📤 SUBIR LIBROS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Envía cualquier PDF al bot\n"
            "y será revisado por el admin.\n"
            "Si es aprobado, aparecerá en\n"
            "el catálogo para todos.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✍️ RESEÑAS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Cuando buscas un libro puedes:\n"
            "• Ver reseñas de otros usuarios\n"
            "• Dejar tu propia reseña (1-5⭐)\n\n"
            "💡 Tip: Puedes guardar libros\n"
            "en favoritos para acceder\n"
            "rápidamente después!"
        )
        await query.message.reply_text(texto)
        return

    if query.data.startswith("cat_"):
        categoria = query.data.replace("cat_", "")
        ruta_cat = os.path.join(CARPETA, categoria)
        archivos = os.listdir(ruta_cat)
        if not archivos:
            await query.message.reply_text(f"😔 La categoría {categoria} está vacía.")
            return
        keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=f"{categoria}/{a}")] for a in archivos]
        await query.message.reply_text(f"📁 {categoria}:\n{len(archivos)} libro(s)", reply_markup=InlineKeyboardMarkup(keyboard))
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

    if query.data.startswith("verreseña_"):
        archivo = query.data.replace("verreseña_", "")
        reseñas = cargar_reseñas()
        res_libro = reseñas.get(archivo, [])
        if not res_libro:
            await query.message.reply_text("😔 Este libro no tiene reseñas aún.")
            return
        texto = f"✍️ Reseñas de {os.path.splitext(os.path.basename(archivo))[0]}:\n\n"
        for r in res_libro[-5:]:
            texto += f"⭐ {'⭐' * r['puntuacion']}\n💬 {r['texto']}\n👤 {r['nombre']}\n\n"
        await query.message.reply_text(texto)
        return

    if query.data.startswith("reseña_"):
        archivo = query.data.replace("reseña_", "")
        context.user_data["reseña_libro"] = archivo
        keyboard = [
            [InlineKeyboardButton("⭐", callback_data=f"punt_1_{archivo}"),
             InlineKeyboardButton("⭐⭐", callback_data=f"punt_2_{archivo}"),
             InlineKeyboardButton("⭐⭐⭐", callback_data=f"punt_3_{archivo}")],
            [InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"punt_4_{archivo}"),
             InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"punt_5_{archivo}")]
        ]
        await query.message.reply_text("¿Qué puntuación le das?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("punt_"):
        partes = query.data.split("_", 2)
        puntuacion = int(partes[1])
        archivo = partes[2]
        context.user_data["reseña_libro"] = archivo
        context.user_data["reseña_puntuacion"] = puntuacion
        context.user_data["esperando_reseña"] = True
        await query.message.reply_text(f"{'⭐' * puntuacion}\n\nAhora escribe tu reseña en el chat:")
        return

    if query.data.startswith("aprobar_"):
        partes = query.data.split("_", 2)
        uid_usuario = partes[1]
        nombre_archivo = partes[2]
        ruta_pendiente = os.path.join(PENDIENTES, f"{uid_usuario}_{nombre_archivo}")
        ruta_destino = os.path.join(CARPETA, nombre_archivo)
        if os.path.exists(ruta_pendiente):
            os.rename(ruta_pendiente, ruta_destino)
            await query.message.reply_text(f"✅ {nombre_archivo} aprobado y agregado.")
            try:
                await context.bot.send_message(int(uid_usuario), f"✅ Tu libro '{nombre_archivo}' fue aprobado y ya está en el catálogo!")
            except:
                pass
        return

    if query.data.startswith("rechazar_"):
        partes = query.data.split("_", 2)
        uid_usuario = partes[1]
        nombre_archivo = partes[2]
        ruta_pendiente = os.path.join(PENDIENTES, f"{uid_usuario}_{nombre_archivo}")
        if os.path.exists(ruta_pendiente):
            os.remove(ruta_pendiente)
            await query.message.reply_text(f"❌ {nombre_archivo} rechazado y eliminado.")
            try:
                await context.bot.send_message(int(uid_usuario), f"❌ Tu libro '{nombre_archivo}' fue rechazado por el administrador.")
            except:
                pass
        return

    ruta = os.path.join(CARPETA, query.data)
    if os.path.exists(ruta):
        nombre_sin_ext = os.path.splitext(os.path.basename(query.data))[0]
        portada = obtener_portada(os.path.basename(query.data))
        keyboard = [[InlineKeyboardButton("⭐ Guardar en favoritos", callback_data=f"addfav_{query.data}")]]
        if portada:
            with open(portada, "rb") as img:
                await query.message.reply_photo(photo=img, caption=f"📖 {nombre_sin_ext}", reply_markup=InlineKeyboardMarkup(keyboard))
        registrar_descarga(query.data)
        registrar_historial(query.from_user.id, query.data)
        with open(ruta, "rb") as f:
            await query.message.reply_document(f)
    else:
        await query.message.reply_text("Archivo no encontrado.")

async def recibir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if esta_bloqueado(update.message.from_user.id):
        return
    if context.user_data.get("esperando_reseña"):
        archivo = context.user_data.get("reseña_libro")
        puntuacion = context.user_data.get("reseña_puntuacion")
        texto_reseña = update.message.text
        reseñas = cargar_reseñas()
        if archivo not in reseñas:
            reseñas[archivo] = []
        reseñas[archivo].append({
            "puntuacion": puntuacion,
            "texto": texto_reseña,
            "nombre": update.message.from_user.full_name
        })
        guardar_reseñas(reseñas)
        context.user_data["esperando_reseña"] = False
        await update.message.reply_text(f"✅ Reseña guardada!\n\n{'⭐' * puntuacion}\n💬 {texto_reseña}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("catalogo", catalogo))
app.add_handler(CommandHandler("top", top))
app.add_handler(CommandHandler("categorias", categorias))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CommandHandler("aleatorio", aleatorio))
app.add_handler(CommandHandler("historial", historial))
app.add_handler(CommandHandler("favoritos", favoritos))
app.add_handler(CommandHandler("estadisticas", estadisticas))
app.add_handler(CommandHandler("ayuda", ayuda))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("eliminar", eliminar))
app.add_handler(CommandHandler("renombrar", renombrar))
app.add_handler(CommandHandler("crearcategoria", crear_categoria))
app.add_handler(CommandHandler("mover", mover))
app.add_handler(CommandHandler("bloquear", bloquear))
app.add_handler(CommandHandler("desbloquear", desbloquear))
app.add_handler(CommandHandler("reporte", reporte))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("usuarios", ver_usuarios))
app.add_handler(MessageHandler(filters.Document.PDF, recibir_documento))
app.add_handler(MessageHandler(filters.PHOTO, recibir_portada))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_texto))
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling(drop_pending_updates=True)