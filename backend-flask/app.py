"""Flask app: UI de chat y endpoints mínimos.

Rutas expuestas:
- GET / -> ping básico
- GET /health -> estado ok
- GET /chat -> UI del chat
- POST /api/upload -> subir PDF para indexarlo (RAG)
- POST /api/message -> pregunta; arma contexto con BM25 y llama Groq
- POST /api/analyze-pdf -> analiza un PDF sin persistir (modo directo desde la UI)
"""

"""Flask app: UI de chat y endpoints mínimos."""

import os
import requests
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from rag import add_pdf_file, retrieve_bm25, make_context, analyze_pdf_in_memory
from llm import build_prompt, call_llm
from utils.phone_utils import normalize_phone 

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de WhatsApp
WHATSAPP_TOKEN = 'EAATU8YKE7vwBQIocRAlj3ZAT5dkQGDKg9KdM7lpBawGciA7yFKzsL7z1uF5iM8rUrGJsZCYUfuKF0C5v3lKxbWPFrypGEdyggB4DugHr2X7Vr0PJQeUdPOaFWj1WIwpRRfwsORR7gQTPZCZBrZBjxfdlsffTtrNbc81XZBN9k49cLJ7gsebeuOJELaS4ZBCXphuVxPvBvHZAVqIs6DkogZAroOirlpWgmBYlvZBGxk8ZB3obni23TW0ZAZAxLRROcEfjx9j9ghwGtSBOTAuwdWVIhD3K33OrVWTmDxNSjt2N2'
PHONE_NUMBER_ID = 756896324184416
VERIFY_TOKEN = 'TTPS-Chatbot-tokenn'

print(f"🔧 Configuración WhatsApp: TOKEN={'✅' if WHATSAPP_TOKEN else '❌'}, PHONE_ID={'✅' if PHONE_NUMBER_ID else '❌'}")


# =============================================================================
# WEBHOOK PRINCIPAL
# =============================================================================

@app.route("/webhook_whatsapp", methods=["GET", "POST"])
def webhook_whatsapp():
    data = request.get_json()

    # Detectar mensajes entrantes (ignorar statuses)
    if "messages" not in data["entry"][0]["changes"][0]["value"]:
        print("ℹ️ Webhook recibido sin mensajes (status/update)")
        return "ok", 200

    message_obj = data["entry"][0]["changes"][0]["value"]["messages"][0]
    sender = message_obj["from"]
    message = message_obj.get("text", {}).get("body", "")

    # Normalización nueva
    from utils.phone_utils import normalize_phone
    e164, wa_id, valid = normalize_phone(sender)

    print(f"\n📩 Webhook recibido")
    print(f"👤 Raw: {sender}")
    print(f"📌 e164: {e164}")
    print(f"📌 whatsapp_id: {wa_id}")
    print(f"✔ válido: {valid}")

    # Si no se pudo normalizar => fallback
    if not valid:
        print("⚠ No se pudo normalizar el número, usando raw")
        wa_id = sender

    # Respuesta por defecto
    response = (
        "🤖 He recibido tu mensaje. Actualmente no tengo documentos cargados. "
        "Podés subir PDFs desde la interfaz web."
    )

    send_whatsapp_message(f"whatsapp:{wa_id}", response)

    return "ok", 200


# =============================================================================
# FUNCIONES DE NORMALIZACIÓN PARA NÚMEROS ARGENTINOS
# =============================================================================
"""
def normalize_argentine_number(number):
    if number.startswith("whatsapp:"):
        number = number.replace("whatsapp:", "")

    print(f"🔍 NORMALIZACIÓN - Entrada: {number} (len: {len(number)})")

    # Caso general Argentina móvil con 9 → removerlo
    if number.startswith("549") and len(number) > 4:
        normalized = "54" + number[3:]
        print(f"🔍 Normalizado móvil AR: {number} → {normalized}")
        return normalized

    # Ya normalizado (54 + resto)
    if number.startswith("54") and len(number) > 4:
        print(f"🔍 Ya normalizado: {number}")
        return number

    print(f"⚠ Formato no reconocido, devolviendo original")
    return number
"""

# =============================================================================
# FUNCIÓN DE ENVÍO DE MENSAJES WHATSAPP
# =============================================================================
def send_whatsapp_message(to, message):
    """
    Envía un mensaje por WhatsApp asegurando normalización correcta.
    Acepta formatos: "549..." "whatsapp:549..." "5422..." etc.
    """

    # Normalizar SIEMPRE primero
    raw, wa_id, valid = normalize_phone(to)
    whatsapp_to = f"whatsapp:{wa_id}"

    if not valid:
        print(f"⚠ Número no válido: {to}")
        return False

    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠ Falta WHATSAPP_TOKEN o PHONE_NUMBER_ID")
        return False

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": whatsapp_to,
        "type": "text",
        "text": {"body": message},
    }

    print(f"🔍 Enviando mensaje a {whatsapp_to}")
    print(f"🔍 Payload: {payload}")

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        print(f"🔍 Status: {resp.status_code}")
        print(f"🔍 Response: {resp.text}")

        if resp.status_code == 200:
            print("✅ Mensaje enviado correctamente")
            return True

        # Manejo detallado de errores API
        try:
            error = resp.json().get("error", {})
            print(f"❌ ERROR ({error.get('code')}): {error.get('message')}")
        except:
            print("❌ Error no parseable")

        return False

    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False


# =============================================================================
# FUNCION DE PROCESAMIENTO DE MENSAJES WHATSAPP -> RESPUESTAS INTELIGENTES
# =============================================================================
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
            chunks = retrieve_bm25(message, top_k=3)
            if chunks:
                context = make_context(chunks, max_chars=1500)
                prompt = build_prompt(message, context)
                respuesta = call_llm(prompt)
                return f"🤖 {respuesta}"
            else:
                return ("🤖 He recibido tu mensaje. " +
                       "Actualmente no tengo documentos cargados para consultar. " +
                       "Puedes subir documentos PDF en la interfaz web.")
        except Exception as e:
            print(f"Error en RAG: {e}")
            return f"🤖 Recibí: '{message}'. Estoy procesando tu consulta..."

# =============================================================================
# ENDPOINTS DE PRUEBA Y DIAGNÓSTICO
# =============================================================================


@app.route("/test-send-message/<number>")
def test_send_message(number):
    return jsonify({
        "sent": send_whatsapp_message(number, "🔍 Test OK"),
        "normalized": normalize_phone(number)
    })



@app.get("/")
def root():
    return jsonify({"message": "Hola desde Flask con Poetry!"})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/message")
def post_message():
    """Recibe una pregunta, recupera contexto (BM25) y llama al LLM.

    Body JSON:
    - message: str (obligatorio)
    - top_k: int (opcional)
    - max_context_chars: int (opcional)
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 415
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if message is None:
        return jsonify({"error": "Falta el campo 'message'"}), 400

    try:
        default_top_k = int(os.getenv("RAG_TOP_K", "8"))
    except Exception:
        default_top_k = 8
    try:
        top_k = int(data.get("top_k", default_top_k))
    except Exception:
        top_k = default_top_k

    max_context_chars = data.get("max_context_chars")
    try:
        max_context_chars = int(max_context_chars) if max_context_chars is not None else None
    except Exception:
        max_context_chars = None

    chunks = retrieve_bm25(message, top_k=top_k)
    context = make_context(chunks, max_chars=max_context_chars)

    prompt = build_prompt(message, context)
    llm_answer = call_llm(prompt)

    result = {
        "rag": {
            "chunks": [
                {"document_id": c.document_id, "chunk_index": c.chunk_index, "score": c.score}
                for c in chunks
            ],
            "context_chars": len(context),
            "top_k": top_k,
        },
        "answer": llm_answer,
    }
    return jsonify({"ok": True, **result})


@app.get("/chat")
def chat_page():
    return render_template("chat.html")


@app.post("/api/upload")
def upload_pdf():
    """Sube un PDF (multipart/form-data campo 'file'), extrae texto y lo indexa.
    Devuelve document_id y cantidad de chunks.
    """
    if "file" not in request.files:
        return jsonify({"error": "Falta archivo en 'file'"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    filename = secure_filename(f.filename)
    try:
        file_bytes = f.read()
        doc_id, n_chunks = add_pdf_file(filename, file_bytes)
        resp = {"ok": True, "document_id": doc_id, "filename": filename, "chunks": n_chunks}
        if n_chunks == 0:
            resp["warning"] = "No se extrajo texto del PDF. Puede ser escaneado o estar protegido."
        return jsonify(resp)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/analyze-pdf")
def analyze_pdf():
    """Analiza un PDF enviado en la request (multipart/form-data campo 'file') sin persistirlo.

    Campos esperados:
    - file: pdf
    - question: texto (pregunta)
    - top_k: opcional
    - max_context_chars: opcional
    """
    if "file" not in request.files:
        return jsonify({"error": "Falta archivo en 'file'"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    question = request.form.get("question") or request.form.get("message")
    if not question:
        return jsonify({"error": "Falta el campo 'question'"}), 400

    try:
        default_top_k = int(os.getenv("RAG_TOP_K", "8"))
    except Exception:
        default_top_k = 8
    try:
        top_k = int(request.form.get("top_k", default_top_k))
    except Exception:
        top_k = default_top_k

    max_context_chars = request.form.get("max_context_chars")
    try:
        max_context_chars = int(max_context_chars) if max_context_chars is not None else None
    except Exception:
        max_context_chars = None

    try:
        file_bytes = f.read()
        chunks, context = analyze_pdf_in_memory(file_bytes, question, top_k=top_k, max_context_chars=max_context_chars)

        prompt = build_prompt(question, context)
        llm_answer = call_llm(prompt)

        result = {
            "rag": {
                "chunks": [
                    {"document_id": c.document_id, "chunk_index": c.chunk_index, "score": c.score}
                    for c in chunks
                ],
                "context_chars": len(context),
                "top_k": top_k,
            },
            "answer": llm_answer,
            "ok": True,
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# Endpoints de depuración y análisis directo removidos para simplificar la app
'''
 if __name__ == "__main__":
    # For dev only; in production use a proper WSGI server
    app.run(host="0.0.0.0", port=5000, debug=True)
            filename = secure_filename(f.filename)
            try:
                file_bytes = f.read()
                doc_id, n_chunks = add_pdf_file(filename, file_bytes)
                resp = {"ok": True, "document_id": doc_id, "filename": filename, "chunks": n_chunks}
                if n_chunks == 0:
                    resp["warning"] = "No se extrajo texto del PDF. Puede ser escaneado o estar protegido."
                return jsonify(resp)
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        @app.post("/api/analyze-pdf")
        def analyze_pdf():
            """Analiza un PDF enviado en la request (multipart/form-data campo 'file') sin persistirlo.

            Campos esperados:
            - file: pdf
            - question: texto (pregunta)
            - top_k: opcional
            - max_context_chars: opcional
            """
            if "file" not in request.files:
                return jsonify({"error": "Falta archivo en 'file'"}), 400
            f = request.files["file"]
            if f.filename == "":
                return jsonify({"error": "Nombre de archivo vacío"}), 400

            question = request.form.get("question") or request.form.get("message")
            if not question:
                return jsonify({"error": "Falta el campo 'question'"}), 400

            try:
                default_top_k = int(os.getenv("RAG_TOP_K", "8"))
            except Exception:
                default_top_k = 8
            try:
                top_k = int(request.form.get("top_k", default_top_k))
            except Exception:
                top_k = default_top_k

            max_context_chars = request.form.get("max_context_chars")
            try:
                max_context_chars = int(max_context_chars) if max_context_chars is not None else None
            except Exception:
                max_context_chars = None

            try:
                file_bytes = f.read()
                chunks, context = analyze_pdf_in_memory(file_bytes, question, top_k=top_k, max_context_chars=max_context_chars)

                prompt = build_prompt(question, context)
                llm_answer = call_llm(prompt)

                result = {
                    "rag": {
                        "chunks": [
                            {"document_id": c.document_id, "chunk_index": c.chunk_index, "score": c.score}
                            for c in chunks
                        ],
                        "context_chars": len(context),
                        "top_k": top_k,
                    },
                    "answer": llm_answer,
                    "ok": True,
                }
                return jsonify(result)
            except Exception as e:
                return jsonify({"error": str(e)}), 500


        # Endpoints de depuración y análisis directo removidos para simplificar la app

        if __name__ == "__main__":
            # For dev only; in production use a proper WSGI server
            app.run(host="0.0.0.0", port=5000, debug=True)*/
'''