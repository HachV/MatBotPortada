import os
import io
from PIL import Image, ImageOps
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Esto detecta automáticamente la carpeta exacta donde está guardado este script (.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Une la carpeta del script con el nombre de la imagen de forma segura
MARCO_PATH = os.path.join(BASE_DIR, 'MarcoMatamoros.png')

MEDIDA_FINAL = (1200, 630)

async def procesar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Avisar al usuario que estamos trabajando en ello
    await update.message.reply_text("Procesando tu imagen, un momento...")

    try:
        # 1. Obtener la foto en su máxima resolución (el último elemento del array)
        archivo = await update.message.photo[-1].get_file()
        foto_bytes = await archivo.download_as_bytearray()
        
        # 2. Abrir la foto del usuario desde la memoria
        foto_usuario = Image.open(io.BytesIO(foto_bytes)).convert("RGBA")
        
        # Recortar y centrar la foto del usuario a 1200x630 (ImageOps.fit hace la magia)
        foto_base = ImageOps.fit(foto_usuario, MEDIDA_FINAL, Image.Resampling.LANCZOS)
        
        # 3. Cargar el marco (banner de Matamoros)
        marco = Image.open(MARCO_PATH).convert("RGBA")
        
        # Al ser un banner inferior, ajustamos su ancho a 1200 manteniendo su proporción de alto
        proporcion = MEDIDA_FINAL[0] / float(marco.width)
        alto_marco = int(float(marco.height) * float(proporcion))
        marco_redimensionado = marco.resize((MEDIDA_FINAL[0], alto_marco), Image.Resampling.LANCZOS)
        
        # Crear una capa transparente del tamaño final (1200x630)
        capa_marco = Image.new("RGBA", MEDIDA_FINAL, (0, 0, 0, 0))
        
        # Calcular la posición Y para que quede pegado abajo (630 - alto_del_marco)
        posicion_y = MEDIDA_FINAL[1] - alto_marco
        
        # Pegar el banner en la capa transparente en la posición calculada
        capa_marco.paste(marco_redimensionado, (0, posicion_y))
        
        # 4. Superponer el banner sobre la foto del usuario
        imagen_final = Image.alpha_composite(foto_base, capa_marco)
        
        # 5. Guardar el resultado final en memoria (RAM) como JPG
        output = io.BytesIO()
        imagen_final.convert("RGB").save(output, format="JPEG", quality=95)
        output.seek(0) # Regresar el puntero al inicio del archivo
        
        # 6. Enviar la foto de vuelta al usuario
        await update.message.reply_photo(photo=output, caption="¡Aquí tienes tu imagen lista!")
        
    except Exception as e:
        await update.message.reply_text(f"Hubo un error al procesar la imagen. Verifica que sea un formato válido. Error: {e}")

if __name__ == '__main__':
    # Inicializar el bot
    app = Application.builder().token(TOKEN).build()
    
    # Escuchar únicamente los mensajes que contengan fotos, ignorar texto
    app.add_handler(MessageHandler(filters.PHOTO, procesar_foto))
    
    print("Bot en ejecución... Presiona Ctrl+C para detener.")
    app.run_polling()