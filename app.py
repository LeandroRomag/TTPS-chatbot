"""Flask app: UI de chat y endpoints mínimos.

Rutas expuestas:
- GET / -> ping básico
- GET /health -> estado ok
- GET /chat -> UI del chat
- POST /api/upload -> subir PDF para indexarlo (RAG)
- POST /api/message -> pregunta; arma contexto con BM25 y llama Groq
"""

from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
import os
from rag import add_pdf_file, retrieve_bm25, make_context
from llm import build_prompt, call_llm

app = Flask(__name__)

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
    # Requiere JSON: { "message": "..." }
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 415
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if message is None:
        return jsonify({"error": "Falta el campo 'message'"}), 400

    # Recuperación de contexto con RAG
    try:
        default_top_k = int(os.getenv("RAG_TOP_K", "8"))
    except Exception:
        default_top_k = 8
    top_k = int(data.get("top_k", default_top_k))
    max_context_chars = data.get("max_context_chars")
    try:
        max_context_chars = int(max_context_chars) if max_context_chars is not None else None
    except Exception:
        max_context_chars = None

    # Recuperación general sobre los documentos indexados
    chunks = retrieve_bm25(message, top_k=top_k)
    context = make_context(chunks, max_chars=max_context_chars)

    # Construir prompt y llamar al LLM
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
    # Soporta multipart/form-data con campo 'file' (uno por request)
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


# Endpoints de depuración y análisis directo removidos para simplificar la app

if __name__ == "__main__":
    # For dev only; in production use a proper WSGI server
    app.run(host="0.0.0.0", port=5000, debug=True)
