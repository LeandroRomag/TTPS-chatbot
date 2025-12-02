import requests
import os
from utils.phone_utils import normalize_phone
from config import WHATSAPP_TOKEN, PHONE_NUMBER_ID

def send_whatsapp_message(to, message):
    print(to,message)
    e164, wa_id, valid = normalize_phone(to)




    if not valid:
        print("⚠ Número no válido, usando raw:", e164)
        wa_id = e164

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": f"whatsapp:{wa_id}",
        "type": "text",
        "text": {"body": message}
    }
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    print("📤 Enviando →", payload)

    resp = requests.post(url, json=payload, headers=headers)
    print("🔍 Respuesta:", resp.text)

    return resp.status_code == 200