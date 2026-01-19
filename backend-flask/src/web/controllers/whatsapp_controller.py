from flask import Blueprint, request, jsonify
# Importamos la lógica del archivo que acabamos de crear
from src.core.whatsapp_service import process_whatsapp_message, send_whatsapp_message

# Definimos el Blueprint
whatsapp_blueprint = Blueprint('whatsapp', __name__)

# IMPORTANTE: La ruta aquí es '/webhook_whatsapp'
@whatsapp_blueprint.route("/webhook_whatsapp", methods=["GET", "POST"])
def webhook_whatsapp():
    
    # 1. Verificación de Meta (GET)
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        # Asegúrate de que este token coincida con el que pusiste en developers.facebook.com
        if verify_token == "token_ttps_2026": 
            return request.args.get("hub.challenge")
        return "Error de validación", 403

    # 2. Recepción de Mensajes (POST)
    try:
        data = request.get_json(force=True)
        
        # Validar si es un evento de mensaje real
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        if "messages" not in value:
            return "ok", 200 # Es solo un cambio de estado
            
        message_obj = value["messages"][0]
        sender = message_obj["from"]
        text = message_obj.get("text", {}).get("body", "")
        
        if not text:
            return "ok", 200

        print(f"📩 Mensaje recibido de {sender}")
        
        # Usamos la lógica separada
        response = process_whatsapp_message(text, sender)
        
        # Enviamos respuesta
        send_whatsapp_message(sender, response)
        
        return "ok", 200
        
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        return "error", 500
    
"""@whatsapp_blueprint.route("/api/chat", methods=["POST"])
def api_chat():
    """
"""
    Endpoint directo para n8n o pruebas locales.
    Recibe JSON: { "message": "Hola" }
    Devuelve JSON: { "response": "Respuesta del bot..." }
    """
"""
    try:
        data = request.get_json(force=True)
        user_message = data.get("message", "")
        
        if not user_message:
            return jsonify({"response": "⚠️ Mensaje vacío"}), 400

        print(f"💬 Chat API recibido: {user_message}")

        # REUTILIZAMOS TU LÓGICA DE IA (La misma de WhatsApp)
        # Usamos un ID ficticio "api-user"
        bot_response = process_whatsapp_message(user_message, "api-user")

        return jsonify({"response": bot_response})
        
    except Exception as e:
        print(f"❌ Error en API Chat: {e}")
        return jsonify({"error": str(e)}), 500 
        """