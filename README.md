# Chatbot Academico

Este proyecto implementa un **chatbot académico con RAG (Retrieval-Augmented Generation)** que responde consultas de alumnos a través de **WhatsApp Business** utilizando documentos institucionales (PDFs) y una API de la facultad. Tiene como objetivo pasar a produccion en los servidores de la facultad.

🔧 Requisitos

Python: 3.12.3
Node.js	≥ 18
Poetry 
Docker	Recomendado (para n8n y Qdrant)
Ngrok	Para exponer Flask públicamente
Meta Cloud API	Cuenta configurada + Webhook verificado
Una API key de Groq (https://console.groq.com/)

```mermaid
graph LR
A[WhatsApp Usuario] --> B[Meta Cloud API]
B --> C[Flask Webhook]
C --> D[n8n - Workflow RAG]
D --> E[Qdrant - Vector Store]
D --> F[LLM - Groq/OpenAI]
C <-- Respuesta JSON -- D

* Flask recibe mensajes desde WhatsApp (webhook).

* n8n procesa el RAG: chunking, embeddings, búsqueda y generación.

* Qdrant almacena vectores de los documentos.

* Admin Web (Vue) permite subir PDFs y ver logs.

## 📂 Estructura del Repositorio
TTPS-chatbot/
├─ backend-flask/ # Webhook, API interna, normalización números, envío mensajes
├─ n8n/ # Workflows de ingesta + búsqueda + embedding
├─ frontend-admin/ # Panel web para subir docs y ver logs
├─ data/ # Persistencia local (docs y logs)
└─ README.md # Este archivo

## Configuración inicial

1) Instalar dependencias
```powershell
poetry install
```

2) Crear `.env` en la raíz con al menos:
```
GROQ_API_KEY=tu_api_key
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TEMPERATURE=0.2
GROQ_MAX_TOKENS=512

# RAG (tamaños por defecto, ajustables)
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=80
RAG_PER_CHUNK_MAX_CHARS=1600
RAG_TOP_K=10
RAG_CONTEXT_CHARS=20000
```

## Ejecutar en desarrollo

```powershell
poetry run python app.py
```

- API: http://127.0.0.1:5000
- Chat UI: http://127.0.0.1:5000/chat

## Uso

1) Cargar un PDF
- `POST /api/upload` (multipart/form-data) con campo `file`.
- Respuesta: `{ ok, document_id, filename, chunks, warning? }`

2) Preguntar en el chat
- En la UI `/chat`, escribe tu pregunta. Puedes ajustar:
	- Top K (trozos recuperados)
	- Máx. contexto (chars) para esa pregunta
- El backend recupera los trozos relevantes (BM25), arma el contexto y llama a Groq.

3) Vía API
- `POST /api/message`
	- Body JSON mínimo: `{ "message": "tu pregunta" }`
	- Opcionales: `top_k`, `max_context_chars`

Respuesta típica:
```
{
	"ok": true,
	"rag": {
		"chunks": [{ "document_id": 1, "chunk_index": 0, "score": 3.2 }, ...],
		"context_chars": 15432,
		"top_k": 10
	},
	"answer": "..."
}
```

## Endpoints
- `GET /health` -> `{ "status": "ok" }`
- `GET /chat` -> UI del chat
- `POST /api/upload` -> subir PDF
- `POST /api/message` -> pregunta con RAG

## Notas sobre límites y performance
- El límite real lo impone la ventana del modelo (Groq). Como regla práctica, 1 token ≈ 4 caracteres. Deja margen para la respuesta.
- `RAG_CONTEXT_CHARS` limita cuántos caracteres del contexto se envían al LLM. Puedes sobrescribir por petición con `max_context_chars`.
- `RAG_PER_CHUNK_MAX_CHARS` limita el tamaño por chunk para evitar trozos gigantes.
- `RAG_TOP_K` controla cuántos trozos intenta meter. Subirlo aumenta cobertura pero también latencia.

## Solución de problemas
- 429 Too Many Requests (rate limit de Groq): espera y reintenta. La app reintenta con backoff (configurable vía `GROQ_MAX_RETRIES`, `GROQ_BACKOFF_BASE`).
- PDF escaneado sin texto: el extractor intenta PyMuPDF y OCR (si disponible). Si sigue vacío, verás un `warning` en la respuesta de `/api/upload`.
- Base de datos: se usa SQLite en `data/docs.sqlite`. Si quieres reiniciar manualmente, puedes borrar ese archivo con la app detenida.

## Prueba rápida (smoke tests)
```powershell
poetry run python quick_test.py
```
