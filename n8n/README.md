
# 🔗 n8n — Workflows del Sistema RAG

Esta carpeta contiene la configuración de **n8n** para ejecutar:

- Chunking de PDFs
- Generación de embeddings
- Upsert en Qdrant
- Query + Prompting + LLM
- Logging del pipeline

---

### 🚀 Workflows esperados

| Workflow | Ruta Webhook | Función |
|----------|--------------|---------|
| `rag_chat` | `/webhook/chat` | Responder consultas desde Flask |
| `ingest_pdf` | `/webhook/ingest` | Cargar y vectorizar documentos |

---

### 📌 Requisitos

| Herramienta | Requisito |
|-------------|----------|
| Node.js | >= 18 (si modo local) |
| Docker | Recomendado |
| Qdrant Cloud | API Key |
| OpenAI / Groq | API Key |

---

### ▶ Ejecución con Docker 
docker-compose up -d

Luego abrir: 
http://localhost:5678

### Estructura 
n8n/
│ docker-compose.yml
│ workflows/
│ credentials/