# 🤖 WhatsApp Business API Integration - TTPS Chatbot

Esta guía explica cómo configurar y usar la integración de WhatsApp Business API con el chatbot de TTPS.

## Tabla de Contenidos

- [Requisitos Previos](#requisitos-previos)
- [Configuración Inicial](#configuración-inicial)
- [Tipos de Tokens](#tipos-de-tokens)
- [Endpoints Disponibles](#endpoints-disponibles)
- [Flujo de Mensajes](#flujo-de-mensajes)
- [Variables de Entorno](#variables-de-entorno)
- [Solución de Problemas](#solución-de-problemas)
- [Deployment](#deployment)

---

## Requisitos Previos

1. **Cuenta de Meta Developer**
   - Crear una cuenta en [developers.facebook.com](https://developers.facebook.com)
   - Crear una app de tipo "Business"

2. **App de WhatsApp Business configurada**
   - Con acceso a la API de WhatsApp
   - Con números de teléfono Business registrados

3. **Webhook configurado**
   - URL pública del servidor (ej: `https://tu-dominio.com/webhook`)
   - Verify Token seguro (ej: `TTPS-Chatbot-token`)

---

## Configuración Inicial

### Paso 1: Configurar el Webhook en Meta Developer

En tu app de Meta Dashboard:

1. Ve a **WhatsApp → Configuration**
2. En **Webhook** configura:
   - **Callback URL**: `https://tu-dominio.com/webhook`
   - **Verify Token**: Genera uno seguro (ej: `TTPS-Chatbot-token`)
   - **Subscribe Fields**: Selecciona `messages`

3. Verificá el webhook desde tu servidor:
   ```
   GET /webhook?hub.mode=subscribe&hub.challenge=CHALLENGE&hub.verify_token=TOKEN
   ```

### Paso 2: Agregar Números de Prueba

1. En Meta Dashboard → **WhatsApp → Settings**
2. Ve a **Recipient phone numbers**
3. Agrega los números de prueba en formato:
   - **Formato**: `54922155826XX` (sin `+` ni espacios)
   - **República Argentina**: Los números deben ser de tu carrier registrado

### Paso 3: Obtener Tokens

En Meta Dashboard → **Apps → Settings → Basic**, copia:

- **App ID**
- **App Secret**

Para obtener el **Access Token**:

```bash
curl -X POST "https://graph.instagram.com/oauth/access_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "grant_type=client_credentials"
```

## Guarda el token en `WHATSAPP_TOKEN` del `.env`.

## Tipos de Tokens

| Tipo                  | Duración       | Uso Recomendado       |
| --------------------- | -------------- | --------------------- |
| **App Access Token**  | Sin expiración | ✅ Producción         |
| **Long-lived Token**  | 60 días        | ✅ Desarrollo/Staging |
| **User Access Token** | 1-2 horas      | ❌ No recomendado     |

---

## Endpoints Disponibles

### 1. Webhook Principal

```http
POST /webhook
Content-Type: application/json

{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "54922134826XX",
                "type": "text",
                "text": {
                  "body": "Hola, ¿cuál es el horario de Algoritmos?"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

**Respuesta esperada:**

```json
{
  "success": true,
  "message_id": "wamid.xxxxx"
}
```

### 2. Verificación de Webhook

```http
GET /webhook?hub.mode=subscribe&hub.challenge=CHALLENGE_VALUE&hub.verify_token=TOKEN
```

---

## Variables de Entorno

Agrega al `.env`:

```env
# WhatsApp Business API
WHATSAPP_TOKEN=EAAxxxxxxxxxx
PHONE_NUMBER_ID=105xxxxxxxxxxxx
WEBHOOK_VERIFY_TOKEN=TTPS-Chatbot-token

# Opcional - para producción
WHATSAPP_API_VERSION=v18.0
```

---

## Flujo de Mensajes

### Recepción y Procesamiento

```
Usuario envía → Webhook recibe → Validar token → Procesar mensaje → Responder
```

#### 1. Validación del Mensaje

- Verificar que viene de un número autorizado
- Validar formato (texto, media, etc.)
- Normalizar número telefónico

#### 2. Procesamiento Inteligente

El chatbot ejecuta esta lógica:

```
┌─ Comando simple? (ej: "ayuda", "hola")
├─ Consultar RAG en documentos? (búsqueda semántica)
├─ Consultar API UNLP? (materias, horarios, etc.)
└─ Respuesta por defecto
```

#### 3. Normalización de Números

El sistema convierte automáticamente:

```
Internacional → WhatsApp
54 9 2213 48-26 → 5492213482600  ✅

Formato: 549XXXXXXXXXX (17 dígitos con código de país)
```

#### 4. Ejemplo de Flujo Completo

**Usuario envía:**

```
Hola, ¿cuál es el horario de Análisis Matemático?
```

**Sistema:**

1. Recibe en el webhook
2. Identifica como consulta de horarios (RAG + API)
3. No es un comando simple
4. Consulta base de datos UNLP por "Análisis Matemático"
5. Busca en documentos indexados en Qdrant
6. Responde con información actualizada

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



# Usar la URL de ngrok en Meta Developer
