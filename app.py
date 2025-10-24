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

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "TTPS-Chatbot-token"

print(f"🔧 Configuración WhatsApp: TOKEN={'✅' if WHATSAPP_TOKEN else '❌'}, PHONE_ID={'✅' if PHONE_NUMBER_ID else '❌'}")

# =============================================================================
# FUNCIONES DE NORMALIZACIÓN PARA NÚMEROS ARGENTINOS
# =============================================================================

def normalize_argentine_number(number):
    """
    Convierte números argentinos del formato internacional al formato que espera WhatsApp
    CORREGIDO: Conversión precisa 549 -> 5422115
    """
    # Remover prefijo 'whatsapp:' si existe
    if number.startswith('whatsapp:'):
        number = number.replace('whatsapp:', '')
    
    print(f"🔍 NORMALIZACIÓN - Entrada: {number} (len: {len(number)})")
    
    # CASO 1: Formato 549XXXXXXXXX (13 dígitos)
    if number.startswith('549') and len(number) == 13:
        # Ej 54922135826XX -> 542211535827XX
        # Estructura: 54 9 221 35827XX -> 54 221 15 35826XXz
        country_code = '54'
        area_code = number[3:6]    # '221' (posiciones 3,4,5 después de '549')
        mobile_rest = number[6:]   # '35826XX' (desde posición 6)
        
        normalized = f"{country_code}{area_code}15{mobile_rest}"
        print(f"🔍 NORMALIZACIÓN - Convertido: {number} -> {normalized}")
        return normalized
    
    # CASO 2: Ya está en formato correcto (14 dígitos)
    elif number.startswith('54221') and len(number) == 14:
        print(f"🔍 NORMALIZACIÓN - Ya está normalizado: {number}")
        return number
    
    # CASO 3: Cualquier otro formato
    else:
        print(f"⚠️ NORMALIZACIÓN - Formato no manejado: {number} (len: {len(number)})")
        return number

# =============================================================================
# FUNCIÓN DE ENVÍO DE MENSAJES WHATSAPP
# =============================================================================
def send_whatsapp_message(to, message):
    
    """Envía mensaje con mejor logging de errores"""
    normalized_to = normalize_argentine_number(to)
    
    print(f"📤 Enviando a: {to} -> normalizado: {normalized_to}")
    
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ Faltan credenciales WHATSAPP_TOKEN / PHONE_NUMBER_ID")
        return False
        
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp", 
        "to": f"whatsapp:{normalized_to}", 
        "type": "text", 
        "text": {"body": message}
    }
    
    print(f"🔍 URL: {url}")
    print(f"🔍 Payload: {payload}")
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"🔍 Status Code: {resp.status_code}")
        print(f"🔍 Response Headers: {dict(resp.headers)}")
        
        # MOSTRAR EL ERROR COMPLETO
        response_text = resp.text
        print(f"🔍 Response Body: {response_text}")
        
        if resp.status_code == 200:
            print(f"✅ Mensaje enviado exitosamente a {normalized_to}")
            return True
        else:
            # Intentar parsear el error como JSON
            try:
                error_data = resp.json()
                error_code = error_data.get('error', {}).get('code')
                error_message = error_data.get('error', {}).get('message', '')
                error_type = error_data.get('error', {}).get('type', '')
                
                print(f"❌ ERROR DETALLADO:")
                print(f"   Code: {error_code}")
                print(f"   Type: {error_type}")
                print(f"   Message: {error_message}")
                
                if error_code == 131030:
                    print(f"🔒 SOLUCIÓN: Agrega este número EXACTO a Meta Developer: {normalized_to}")
                elif error_code == 131009:
                    print("⏰ Ventana de 24h expirada")
                elif error_code == 131026:
                    print("📵 Número de WhatsApp inválido")
                    
            except Exception as json_error:
                print(f"❌ No se pudo parsear error como JSON: {json_error}")
                print(f"❌ Raw response: {response_text}")
                
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")
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

@app.route("/test-normalization")
def test_normalization():
    """Prueba la normalización de números argentinos"""
    test_cases = [
        "5492215582719",      # Formato internacional con 9
        "54221155582719",     # Formato WhatsApp correcto
        "whatsapp:549221358298",  # Con prefijo
        "541134567890",       # Otro formato (Buenos Aires)
        "5491112345678",      # Otro número
    ]
    
    results = {}
    for num in test_cases:
        normalized = normalize_argentine_number(num)
        results[num] = {
            "normalized": normalized,
            "length_original": len(num),
            "length_normalized": len(normalized)
        }
    
    return jsonify({
        "message": "Prueba de normalización de números argentinos",
        "results": results
    })

@app.route("/test-send-message/<number>")
def test_send_message(number):
    """Prueba enviar mensaje a un número específico"""
    test_message = "🔍 Mensaje de prueba - Normalización Argentina"
    success = send_whatsapp_message(number, test_message)
    
    return jsonify({
        "number": number,
        "normalized": normalize_argentine_number(number),
        "success": success,
        "message": test_message
    })

    # --- TEST WHATSAPP INTEGRATION ---

@app.route("/test-whatsapp")
def test_whatsapp():
    """Endpoint para probar WhatsApp"""
    success = send_whatsapp_message(os.getEnv("TEST_WHATSAPP_NUMBER"), "Hola, prueba desde endpoint")
    return jsonify({"success": success})

# =============================================================================
# WEBHOOK PRINCIPAL
# =============================================================================

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verificado correctamente")
            return challenge, 200
        else:
            print("❌ Token incorrecto")
            return "Token incorrecto", 403
    
    elif request.method == "POST":
        data = request.get_json()
        print("📩 Webhook recibido")
        
        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            # Manejar diferentes tipos de webhooks
            if "messages" in value:
                messages = value["messages"]
                if messages:
                    msg = messages[0]
                    from_number = msg["from"]
                    
                    # Mostrar información de normalización
                    normalized_number = normalize_argentine_number(from_number)
                    print(f"🎯 Número recibido: {from_number} -> normalizado: {normalized_number}")
                    
                    if "text" in msg:
                        text = msg["text"]["body"]
                        print(f"💬 Mensaje de {from_number}: {text}")
                        
                        # Procesar y responder
                        response = process_whatsapp_message(text, from_number)
                        print(f"🤖 Respuesta generada: {response}")
                        
                        # Enviar respuesta (usará normalización automática)
                        success = send_whatsapp_message(from_number, response)
                        
                        if success:
                            print(f"✅ Respuesta enviada exitosamente a {normalized_number}")
                        else:
                            print(f"❌ Error enviando respuesta a {normalized_number}")
                            
                    else:
                        print(f"📎 Mensaje no textual de {from_number}")
                        send_whatsapp_message(from_number, "🤖 Por ahora solo proceso mensajes de texto")
            else:
                print("ℹ️ Webhook de tipo:", list(value.keys()))
                
        except Exception as e:
            print(f"⚠️ Error procesando webhook: {e}")
            print("Datos recibidos:", data)

        return "EVENT_RECEIVED", 200

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