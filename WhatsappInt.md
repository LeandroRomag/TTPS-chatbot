🤖 WhatsApp Business API Integration - TTPS Chatbot
Esta guía explica cómo configurar y usar la integración de WhatsApp Business API con el chatbot de TTPS.

🚀 Requisitos Previos
Cuenta de Meta Developer

App de WhatsApp Business configurada

Número de teléfono verificado para WhatsApp Business

Python 3.8+ y Poetry instalados

⚙️ Configuración Inicial
1. Clonar y Configurar el Proyecto
bash
git clone <repository-url>
cd TTPS-chatbot
poetry install
2. Configurar Variables de Entorno
Crear archivo .env:

env
# WhatsApp Business API
WHATSAPP_TOKEN=tu_token_de_whatsapp_aqui
PHONE_NUMBER_ID=tu_phone_number_id_aqui

# Para testing (opcional)
TEST_WHATSAPP_NUMBER=541234567890

# Groq API
GROQ_API_KEY=tu_groq_api_key_aqui

# Configuración RAG
RAG_TOP_K=8
🔧 Configuración en Meta Developer
1. Configurar Webhook
Ir a Meta Developer → Tu App → WhatsApp → Configuration

En Webhook configura:

URL: https://tu-dominio.com/webhook -> URL de ejemplo 

Verify Token: TTPS-Chatbot-token

Events: Selecciona "messages"

2. Agregar Números de Prueba
En Dashboard → WhatsApp → Settings

En Recipientes de números de teléfono agrega los números de prueba

Formato: 54922155826XX (sin + ni espacios)

3. Tipos de Tokens Disponibles
Tipo	Duración	Uso Recomendado
App Access Token	Sin expiración	✅ Producción
Long-lived Token	60 días	✅ Desarrollo
User Access Token	1-2 horas	Desarrollo

🌐 Endpoints Disponibles
Webhook Principal
POST /webhook - Recibe mensajes de WhatsApp

GET /webhook - Verificación del webhook

💬 Flujo de Mensajes
Recepción de Mensajes
text
Usuario → "Hola" → Webhook (/webhook) → Procesamiento → Respuesta → Usuario
Procesamiento Inteligente
Comandos simples: Saludos, ayuda

RAG: Consultas sobre documentos PDF

Respuesta por defecto: Mensaje genérico

Normalización de Números
El sistema convierte automáticamente:

text
54922134826XX → 542211534826XX
(Formato internacional → Formato WhatsApp)

🛠️ Solución de Problemas
Errores Comunes
❌ Error 190 - Token Expirado
{"error": {"code": 190, "message": "Error validating access token"}}
Solución: Renovar el token en Meta Developer

❌ Error 131030 - Número No Autorizado
{"error": {"code": 131030, "message": "Recipient phone number not in allowed list"}}
Solución: Agregar el número a la lista de destinatarios en Meta Developer

❌ Error 131009 - Ventana Expirada
{"error": {"code": 131009, "message": "Message undeliverable"}}

🚀 Deployment
Con Ngrok (Desarrollo)
bash
ngrok http 5000
# Usar la URL de ngrok en Meta Developer