import os
import requests
from dotenv import load_dotenv
from src.utils.phone_utils import normalize_phone

load_dotenv()

# --- LÓGICA DE PROCESAMIENTO ---

def process_whatsapp_message(message, from_number):
    """
    Versión LIMPIA: Actúa como puente.
    Recibe el mensaje de WhatsApp y se lo entrega crudo al Agente de n8n.
    """
    message_lower = message.lower().strip()
    
    # 1. Comandos simples (Opcional: Respuestas rápidas sin gastar IA)
    if message_lower in ['hola', 'hi', 'buenas']:
        return "¡Hola! 👋 Soy tu asistente de TTPS. Pregúntame sobre el calendario, fechas o noticias."
    
    # 2. Delegar TODO el resto a n8n
    try:
        ask_n8n = os.getenv("N8N_WEBHOOK_ASK")
        if not ask_n8n:
            return "❌ Error: Falta configurar N8N_WEBHOOK_ASK."

        # Payload simple: Solo el mensaje y quién lo envía
        payload = {
            "message": message,
            "sessionId": from_number   # Para mantener la memoria de la conversación
        }

        print(f"🔄 Consultando a n8n Agente: {message}")
        r = requests.post(ask_n8n, json=payload, timeout=60)

        if r.status_code == 200:
            data = r.json()
            return data.get("output") or data.get("text") or data.get("response") or "🤖 n8n respondió, pero sin texto."
        else:
            print(f"❌ Error n8n: {r.status_code} - {r.text}")
            return "Lo siento, mi cerebro (n8n) tuvo un error procesando tu solicitud."

    except Exception as e:
        print(f"❌ Excepción python: {e}")
        return "Ocurrió un error interno de conexión."


# --- ENVÍO DE MENSAJES (Se mantiene igual) ---

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

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        print(f"❌ Error Meta: {r.text}")
        return False
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False