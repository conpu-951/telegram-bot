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
ADMIN_ID = 6262593562

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

def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f)

def registrar_usuario(user):
    usuarios = cargar_usuarios()
    uid = str(user.id)
    if uid not in usuarios:
        usuarios[uid] = {
            "nombre": user.full_name,
            "username": user.username or "sin username"
        }
        guardar_usuarios(usuarios)

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
    registrar_usuario(update.message.from_user)
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
    registrar_usuario(update.message.from_user)
    archivos = []
    for item in os.listdir(CARPETA):
        ruta = os.path.join(CARPETA, item)
        if os.path.isfile(ruta):
            archivos.append(item)
        elif os.path.isdir(ruta):
            for archivo in os.listdir(ruta):
                archivos.append(f"{item}/{archivo}")
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
    archivos = []
    for item in os.listdir(CARPETA):
        ruta = os.path.join(CARPETA, item)
        if os.path.isfile(ruta) and palabra in item.lower():
            archivos.append(item)
        elif os.path.isdir(ruta):
            for archivo in os.listdir(ruta):
                if palabra in archivo.lower():
                    archivos.append(f"{item}/{archivo}")
    if not archivos:
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
    keyboard = [[InlineKeyboardButton(f"📖 {a}", callback_data=a)] for a in archivos]
    await update.message.reply_text(
        f"╔═══════════════════════╗\n"
        f"   ✅ LIBRO ENCONTRADO 🧐\n"
        f"╚═══════════════════════╝\n\n"
        f"📚 Se encontraron {len(archivos)} resultado(s)\n\n"
        f"👇 Presiona para descargar:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def favoritos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registrar_usuario(update.message.from_user)
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
    registrar_usuario(update.message.from_user)
    stats = cargar_stats()
    usuarios = cargar_usuarios()
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
        await update.message.reply_text("⛔ No tienes permiso para usar este comando.")
        return
    usuarios = cargar_usuarios()
    categorias = [f for f in os.listdir(CARPETA) if os.path.isdir(os.path.join(CARPETA, f))]
    await update.message.reply_text(
        "╔═══════════════════════╗\n"
        "   👤 PANEL DE ADMIN\n"
        "╚═══════════════════════╝\n\n"
        f"👥 Usuarios: {len(usuarios)}\n"
        f"📁 Categorias: {len(categorias)}\n\n"
        "Comandos disponibles:\n\n"
        "📤 Enviar PDF para agregar libro\n\n"
        "🗑️ /eliminar nombre.pdf\n\n"
        "✏️ /renombrar actual.pdf nuevo.pdf\n\n"
        "📁 /crearcategoria nombre\n\n"
        "📂 /mover libro.pdf categoria\n\n"
        "📢 /broadcast mensaje\n\n"
        "📋 /usuarios\n"
    )

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
        await update.message.reply_text(
            "✏️ Uso: /renombrar actual.pdf nuevo.pdf\n\n"
            "Ejemplo:\n"
            "/renombrar casa.pdf mi_casa.pdf"
        )
        return
    actual = context.args[0]
    nuevo = context.args[1]
    ruta_actual = os.path.join(CARPETA, actual)
    ruta_nueva = os.path.join(CARPETA, nuevo)
    if os.path.exists(ruta_actual):
        os.rename(ruta_actual, ruta_nueva)
        await update.message.reply_text(f"✅ Renombrado:\n{actual} → {nuevo}")
    else:
        await update.message.reply_text(f"😔 No se encontró {actual}.")

async def crear_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text(
            "✏️ Uso: /crearcategoria nombre\n\n"
            "Ejemplo:\n"
            "/crearcategoria Motivacion"
        )
        return
    nombre = " ".join(context.args)
    ruta = os.path.join(CARPETA, nombre)
    if os.path.exists(ruta):
        await update.message.reply_text(f"😔 La categoría {nombre} ya existe.")
    else:
        os.makedirs(ruta)
        await update.message.reply_text(f"✅ Categoría {nombre} creada correctamente.")

async def mover(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "✏️ Uso: /mover libro.pdf Categoria\n\n"
            "Ejemplo:\n"
            "/mover casa.pdf Motivacion"
        )
        return
    libro = context.args[0]
    categoria = context.args[1]
    ruta_origen = os.path.join(CARPETA, libro)
    ruta_destino = os.path.join(CARPETA, categoria, libro)
    if not os.path.exists(ruta_origen):
        await update.message.reply_text(f"😔 No se encontró {libro}.")
        return
    if not os.path.exists(os.path.join(CARPETA, categoria)):
        await update.message.reply_text(f"😔 La categoría {categoria} no existe.\nCrea con /crearcategoria {categoria}")
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
    enviados = 0
    fallidos = 0
    for uid in usuarios:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 Mensaje del administrador:\n\n{mensaje}"
            )
            enviados += 1
        except:
            fallidos += 1
    await update.message.reply_text(
        f"✅ Mensaje enviado\n\n"
        f"📤 Enviados: {enviados}\n"
        f"❌ Fallidos: {fallidos}"
    )

async def ver_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ No tienes permiso.")
        return
    usuarios = cargar_usuarios()
    if not usuarios:
        await update.message.reply_text("😔 No hay usuarios registrados aún.")
        return
    texto = (
        "╔═══════════════════════╗\n"
        "   📋 LISTA DE USUARIOS\n"
        "╚═══════════════════════╝\n\n"
        f"👥 Total: {len(usuarios)}\n\n"
    )
    for uid, datos in list(usuarios.items())[:20]:
        texto += f"👤 {datos['nombre']}\n"
        texto += f"   @{datos['username']}\n\n"
    await update.message.reply_text(texto)

async def recibir_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    doc = update.message.document
    if not doc.file_name.endswith(".pdf"):
        await update.message.reply_text("⚠️ Solo se aceptan archivos PDF.")
        return
    archivo = await doc.get_file()
    ruta = os.path.join(CARPETA, doc.file_name)
    await archivo.download_to_drive(ruta)
    await update.message.reply_text(f"✅ {doc.file_name} agregado correctamente.")
    usuarios = cargar_usuarios()
    nombre_sin_ext = os.path.splitext(doc.file_name)[0]
    for uid in usuarios:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"🔔 Nuevo libro disponible!\n\n📖 {nombre_sin_ext}\n\nEscribe /lista para verlo."
            )
        except:
            pass

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
        nombre_sin_ext = os.path.splitext(query.data)[0]
        portada_jpg = os.path.join(PORTADAS, f"{nombre_sin_ext}.jpg")
        portada_png = os.path.join(PORTADAS, f"{nombre_sin_ext}.png")
        keyboard = [[InlineKeyboardButton("⭐ Guardar en favoritos", callback_data=f"addfav_{query.data}")]]
        if os.path.exists(portada_jpg):
            with open(portada_jpg, "rb") as img:
                await query.message.reply_photo(
                    photo=img,
                    caption=f"📖 {nombre_sin_ext}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        elif os.path.exists(portada_png):
            with open(portada_png, "rb") as img:
                await query.message.reply_photo(
                    photo=img,
                    caption=f"📖 {nombre_sin_ext}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        registrar_descarga(query.data)
        with open(ruta, "rb") as f:
            await query.message.reply_document(f)
    else:
        await query.message.reply_text("Archivo no encontrado.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("lista", lista))
app.add_handler(CommandHandler("buscar", buscar))
app.add_handler(CommandHandler("favoritos", favoritos))
app.add_handler(CommandHandler("estadisticas", estadisticas))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("eliminar", eliminar))
app.add_handler(CommandHandler("renombrar", renombrar))
app.add_handler(CommandHandler("crearcategoria", crear_categoria))
app.add_handler(CommandHandler("mover", mover))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("usuarios", ver_usuarios))
app.add_handler(MessageHandler(filters.Document.PDF, recibir_documento))
app.add_handler(CallbackQueryHandler(boton))
print("Bot funcionando...")
app.run_polling(drop_pending_updates=True)