import os
import re
import requests
from html import unescape
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIGURACIÓN DE ENDPOINTS ---
ENDPOINTS = {
    "timeline": {
        "url": "https://gestiondocente.info.unlp.edu.ar/api/v2/timeline.json",
        "keywords": ["noticia", "evento", "extension", "vencimiento"]
    },
    "calendario": {
        "url": "https://gestionapp.info.unlp.edu.ar/api/CALENDARIO_ACADEMICO",
        "keywords": ["fecha", "calendario", "cuando", "cronograma"]
    },
    # ... (Agrega el resto de endpoints del código de tu compañero)
}

# --- 2. FUNCIONES DE LIMPIEZA ---
def clean_html(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# --- 3. LÓGICA DE NEGOCIO (Scraping) ---
def select_endpoints(question):
    q = question.lower()
    selected = []
    for cfg in ENDPOINTS.values():
        if any(k in q for k in cfg["keywords"]):
            selected.append(cfg["url"])
    return selected[:2]

def fetch_dynamic_context(question):
    urls = select_endpoints(question)
    context_blocks = []
    for url in urls:
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            text = ""

            if "timeline" in url:
                text = extract_timeline_text(data, question)

            elif "CALENDARIO_ACADEMICO" in url:
                text = extract_calendar_text(data, question)

            elif "materias" in url:
                text = extract_materias_text(data, question)

            elif "estadoactual" in url:
                text = extract_estado_text(data, question)

            elif "PLANES_ESTUDIOS" in url:
                text = extract_planes_text(data, question)

            if text:
                context_blocks.append(text)

        except Exception as e:
            print("⚠ Error fetch:", e)

    return "\n".join(context_blocks)

def extract_planes_text(data, question): 
    pass
def extract_estado_text(data, question):
    pass
def extract_materias_text(data, question):
    pass

def extract_calendar_text(data, question):
    results = []
    q = question.lower()

    try:
        for item in data:  # 👈 data es una lista
            nombre = item.get("nombre", "")
            contenido = clean_html(item.get("contenido", ""))
            texto = contenido.lower()

            # keywords relevantes reales
            keywords = ["inscripcion", "examen", "final", "cursada", "semestre", "feriado", "vacaciones", "inicio", "fin", "clases", "fecha"]

            if any(k in q for k in keywords) and any(k in texto for k in keywords):
                results.append(
                    f"📘 {nombre}\n{contenido}"
                )

    except Exception as e:
        print("⚠ Error calendario:", e)

    return "\n".join(results[:2])  # 🔥 límite duro
        

def extract_timeline_text(data, question):
    results = []
    q = question.lower()

    try:
        eventos = data["_embedded"]["content"]
        for e in eventos:
            n = e["_embedded"]["noticia"]
            texto = f"{n['titulo']} {n['cuerpo']}".lower()

            if any(k in texto for k in q.split()):
                results.append(
                    f"- {n['fecha']}: {clean_html(n['titulo'])}\n{clean_html(n['cuerpo'])}"
                )

    except Exception as e:
        print("⚠ Error timeline:", e)

    return "\n".join(results[:3])
# --- 4. ENVÍO DE MENSAJES ---
from src.utils.phone_utils import normalize_phone 

def send_whatsapp_message(to, message):
    e164, wa_id, valid = normalize_phone(to)

    if not valid:
        print(f"⚠ Número inválido: {to}")
        return False

    whatsapp_to = f"whatsapp:{wa_id}"

    PHONE_ID = os.getenv("PHONE_NUMBER_ID")
    TOKEN = os.getenv("WHATSAPP_TOKEN")

    if not PHONE_ID or not TOKEN:
        print("❌ Falta PHONE_NUMBER_ID o WHATSAPP_TOKEN")
        return False

    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": whatsapp_to,
        "type": "text",
        "text": {"body": message},
    }

    print(f"📤 Enviando mensaje a {whatsapp_to}")
    print(f"📦 Payload: {payload}")

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)

        print(f"🔍 Status: {r.status_code}")
        print(f"🔍 Respuesta API: {r.text}")

        if r.status_code == 200:
            print("✅ Mensaje enviado correctamente")
            return True

        return False

    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False




def process_whatsapp_message(message, from_number):
    """
    Procesa el mensaje y genera una respuesta inteligente
    
    Args:
        message (str): Mensaje recibido del usuario
        from_number (str): Número que envió el mensaje
    
    Returns:
        str: Respuesta generada
    """
    message_lower = message.lower().strip()
    
    # Comandos simples
    if message_lower in ['hola', 'hi', 'hello', 'buenas']:
        return "¡Hola! 👋 Soy tu asistente de TTPS. ¿En qué puedo ayudarte?"
    
    elif message_lower in ['ayuda', 'help', 'comandos']:
        return ("🤖 *Comandos disponibles:*\n"
                "• Preguntar sobre documentos: escribe tu pregunta directamente\n" 
                "• Saludar: hola\n"
                "• Ayuda: ayuda")
    
    # Intentar usar RAG para responder preguntas
    else:
        try:
            ask_n8n = os.getenv("N8N_WEBHOOK_ASK")
            if not ask_n8n:
                return "❌ No está configurado el webhook de n8n."

            # 🔥 NUEVO
            dynamic_context = fetch_dynamic_context(message)

            payload = {
                "message": message,
                "from_number": from_number,
                "dynamic_context": dynamic_context
           }

            r = requests.post(ask_n8n, json=payload, timeout=60)

            if r.status_code == 200:
                resp_json = r.json()
                return resp_json.get("answer", "❌ Respuesta vacía.")
            else:
                return f"❌ Error al procesar la pregunta ({r.status_code})."

        except Exception as e:
            return f"❌ Excepción al procesar la pregunta: {e}"
