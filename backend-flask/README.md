# 🧠 Backend Flask — Webhook & API Interna

Este módulo expone los endpoints del sistema y actúa como puente entre **WhatsApp (Meta API)** y los workflows de **n8n**.

### 🚀 Funcionalidades principales

| Función | Descripción |
|--------|------------|
| Webhook WhatsApp | Recibe mensajes entrantes y normaliza números argentinos. |
| Proxy a n8n | Envía consultas al workflow RAG. |
| Upload PDFs | Recibe archivos desde el panel admin y los envía a n8n para indexar. |
| Logging | Registra interacciones y errores. |

---

### 📌 Endpoints principales

| Ruta | Método | Uso |
|------|--------|-----|
| `/webhook_whatsapp` | `GET/POST` | Webhook oficial de WhatsApp |
| `/api/message` | `POST` | Mensajes manuales desde UI |
| `/api/upload` | `POST` | Carga y guarda PDFs |
| `/test-send-message/<num>` | `GET` | Prueba de envío directo |

---

### 🔧 Variables de entorno

Crear `.env`:

WHATSAPP_TOKEN=...
PHONE_NUMBER_ID=...
VERIFY_TOKEN=...
N8N_WEBHOOK_CHAT=http://localhost:5678/webhook/chat
N8N_WEBHOOK_INGEST=http://localhost:5678/webhook/ingest


---

### ▶ Cómo correr

```bash
cd backend-flask
poetry install
poetry run python app.py

🧩 Futuras mejoras

Autenticación admin

Persistencia en SQLite

Webhooks retry-safe