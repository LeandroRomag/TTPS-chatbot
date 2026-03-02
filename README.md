# Chatbot Académico - Facultad de Informática UNLP

Asistente conversacional para estudiantes de la Facultad de Informática de la UNLP. Responde consultas sobre materias, horarios, correlativas, planes de estudio y documentos académicos vía WhatsApp.

## Arquitectura

```
WhatsApp → n8n (agente IA + tools) → Flask Backend → Qdrant (búsqueda semántica)
                                    ↓
                          APIs públicas UNLP
```

- **n8n**: orquesta el agente de IA (Groq/Gemini) y las herramientas
- **Flask**: backend que procesa PDFs, genera embeddings y expone la API de búsqueda
- **Qdrant**: base de datos vectorial para búsqueda semántica en documentos
- **HuggingFace**: modelo `intfloat/multilingual-e5-large` para embeddings

---

## Requisitos

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- Docker (para n8n y Qdrant)
- Cuenta en [HuggingFace](https://huggingface.co/) (opcional, hay fallback local)
- Cuenta en [Groq](https://console.groq.com/) o Google Gemini (https://aistudio.google.com/api-keys) RECOMENDADO

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd backend-flask
```

### 2. Instalar dependencias Python

```bash
poetry install
```

### 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
HUGGINGFACE_API_TOKEN=hf_xxxxxxxxxxxx   # acelera la generación de embeddings
QDRANT_URL=http://localhost:6333
SECRET_KEY=una-clave-secreta-cualquiera
DATABASE_URL=sqlite:///db.sqlite3        # O tu URL de base de datos
```

### 4. Levantar Qdrant con Docker

```bash
En proceso...
```

### 5. Inicializar la base de datos y correr Flask

```bash
poetry run py app.py
```

Flask va a quedar corriendo en `http://0.0.0.0:5000`. Verificá que diga:
```
* Running on http://127.0.0.1:5000
* Running on http://192.168.X.X:5000
```

---

## Configurar n8n

### 1. Levantar n8n con Docker

```bash
En proceso..
```

Accedé a `http://localhost:5678`.

### 2. Importar el workflow

En n8n: **Settings → Import workflow** → subí el archivo `chatbot_unlp v8` del repositorio dentro de la carpeta /n8n/workflows

### 3. Configurar credenciales en n8n

Dentro del workflow configurá:
- **Groq API**: tu API key de Groq (modelo `llama-3.3-70b-versatile`)
- O **Google Gemini API**: como alternativa al modelo de lenguaje

### 4. Apuntar los tools al backend Flask

Los tools `buscar_en_documentos` y `consultar_documentos_disponibles` usan la IP local de tu máquina (no `localhost`, ya que n8n corre en Docker):

```javascript
// Reemplazá con tu IP local (la que muestra Flask al iniciar)
url: 'http://192.168.X.X:5000/document/api/search'
url: 'http://192.168.X.X:5000/document/api/list'


## Cargar documentos académicos

1. Abrí `http://localhost:5000` en el navegador
2. Iniciá sesión con tu usuario
3. Ir a **Documentos → Nuevo documento**
4. Subí un PDF (programa de materia, reglamento, etc.)
5. El sistema automáticamente:
   - Divide el PDF en chunks por secciones
   - Genera embeddings con `multilingual-e5-large` usando el prefijo `passage: `
   - Indexa los vectores en Qdrant

---

## Cómo funciona la búsqueda semántica

El modelo `multilingual-e5-large` requiere prefijos específicos para funcionar correctamente:

| Uso | Prefijo |
|-----|---------|
| Indexar documentos | `passage: ` |
| Consultas de búsqueda | `query: ` |

Sin estos prefijos los vectores son incompatibles entre sí y la búsqueda devuelve resultados irrelevantes.

---

## Herramientas disponibles en el agente

| Tool | Descripción |
|------|-------------|
| `consultar_materias` | Busca materias por nombre y devuelve su slug |
| `consultar_detalle_materia` | Horarios, inicio de cursada y programa de una materia |
| `consultar_horarios_aulas` | Días, horarios y aulas asignadas |
| `consultar_cartelera_materia` | Novedades, fechas de finales e inscripciones |
| `consultar_calendario` | Calendario académico oficial |
| `consultar_planes` | Planes de estudio y correlativas por carrera |
| `consultar_novedades_general` | Noticias generales de la facultad |
| `consultar_ocupacion_aula` | Disponibilidad de un aula específica |
| `buscar_en_documentos` | Búsqueda semántica en PDFs cargados |
| `consultar_documentos_disponibles` | Lista los PDFs indexados con sus IDs |

---

