import requests
import os

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

def handle_whatsapp_message(message, sender):
    url = N8N_WEBHOOK_URL
    payload = {
        "message": message,
        "from": sender
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        return data.get("reply", "No entendí tu mensaje 😕")
    except Exception as e:
        print("❌ Error llamando a n8n:", e)
        return "Error procesando tu mensaje."