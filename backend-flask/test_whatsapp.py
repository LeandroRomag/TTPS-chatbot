import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def send_whatsapp_message(to, message):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Faltan credenciales")
        return False
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": f"whatsapp:{to}", "type": "text", "text": {"body": message}}
    resp = requests.post(url, headers=headers, json=payload)
    print(resp.status_code, resp.text)
    return resp.status_code == 200

send_whatsapp_message("54221153582618", "Hola, prueba standalone")
