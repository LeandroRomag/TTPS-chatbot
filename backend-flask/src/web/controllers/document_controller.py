from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from src.core.board.document import Document
from src.core.database import db
from src.web.controllers.auth_controller import login_required 
import os
import requests
import hashlib  # <--- NUEVA IMPORTACIÓN
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- CONFIGURACIÓN DE EXTENSIONES PERMITIDAS ---
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- NUEVA FUNCIÓN AUXILIAR: CALCULAR HASH ---
def calculate_file_hash(file_stream):
    """Calcula el hash SHA256 de un archivo para verificar duplicados por contenido."""
    sha256_hash = hashlib.sha256()
    # Leemos el archivo en bloques de 4KB para no saturar la memoria
    for byte_block in iter(lambda: file_stream.read(4096), b""):
        sha256_hash.update(byte_block)
    
    # IMPORTANTE: Reiniciar el puntero del archivo al inicio después de leerlo
    file_stream.seek(0)
    return sha256_hash.hexdigest()

document_blueprint = Blueprint("document", __name__, url_prefix="/document")

@document_blueprint.get("/")
@login_required
def index():
    docs = db.session.query(Document).order_by(Document.uploaded_at.desc()).all()
    return render_template("document/index.html", documents=docs, active_page='documentos')

@document_blueprint.get("/create")
@login_required
def create():
    return render_template("document/create.html", active_page='documentos')

@document_blueprint.post("/create")
@login_required
def create_post():
    # 1. Obtener datos
    title = request.form.get("title")
    description = request.form.get("description")
    
    # Validaciones básicas
    if not description:
        flash("La descripción es obligatoria", "danger")
        return render_template("document/create.html", active_page='documentos')

    # Validación: Nombre único (Título)
    if title:
        existing_doc = db.session.query(Document).filter(Document.title == title).first()
        if existing_doc:
            flash(f"El nombre '{title}' ya está en uso. Por favor elige otro.", "danger")
            return redirect(url_for("document.create"))

    if "file" not in request.files:
        flash("No se envió ningún archivo", "danger")
        return redirect(url_for("document.create"))
    
    file = request.files["file"]
    
    if file.filename == "":
        flash("Nombre de archivo vacío", "danger")
        return redirect(url_for("document.create"))

    # Validación: Extensión permitida
    if not allowed_file(file.filename):
        flash("Formato no válido. Solo se permiten archivos: PDF, Word, Texto (.txt) o Markdown (.md)", "danger")
        return redirect(url_for("document.create"))

    if file:
        # --- NUEVA VALIDACIÓN: VERIFICAR DUPLICADO POR CONTENIDO (HASH) ---
        try:
            # 1. Calculamos el hash del archivo que se está subiendo ahora
            incoming_hash = calculate_file_hash(file)
            
            # 2. Obtenemos todos los documentos existentes para comparar
            # (Nota: Si tienes miles de archivos, lo ideal sería guardar el hash en la BD para no leer discos)
            existing_docs = db.session.query(Document).all()
            
            for doc in existing_docs:
                if doc.file_path and os.path.exists(doc.file_path):
                    # Abrimos cada archivo existente y calculamos su hash
                    with open(doc.file_path, 'rb') as f_existing:
                        existing_hash = calculate_file_hash(f_existing)
                        
                        # Si los hashes coinciden, el contenido es idéntico
                        if incoming_hash == existing_hash:
                            flash(f"Este archivo ya existe en el sistema (Documento: '{doc.title}'). No se permite subir duplicados.", "warning")
                            return redirect(url_for("document.create"))
        except Exception as e:
            print(f"Error verificando duplicados: {e}")
            # Si falla la verificación, permitimos continuar o lanzamos error según prefieras.
            # Aquí solo lo logueamos para no bloquear el flujo crítico si falla la lectura de disco.

        save_path = None
        try:
            # --- PASO 1: GUARDAR ARCHIVO FÍSICO TEMPORALMENTE ---
            filename = secure_filename(file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Doble chequeo por si el nombre de archivo ya existe físicamente (aunque el contenido sea distinto)
            if os.path.exists(save_path):
                # Generar un nombre único si colisiona
                base, ext = os.path.splitext(filename)
                import uuid
                filename = f"{base}_{uuid.uuid4().hex[:6]}{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)

            file.save(save_path)

            # --- PASO 2: PREPARAR BASE DE DATOS (SIN COMMIT) ---
            new_doc = Document(
                title=title,
                description=description,
                file_path=save_path,
                uploaded_by=session["user_id"] 
            )
            db.session.add(new_doc)
            
            db.session.flush() 

            # --- PASO 3: INTENTAR ENVIAR A N8N ---
            n8n_webhook = os.getenv("N8N_WEBHOOK_PDF")
            
            if not n8n_webhook:
                raise Exception("La URL del Webhook de n8n no está configurada.")

            n8n_success = False
            
            with open(save_path, 'rb') as f:
                # Determinamos el content-type correcto
                ext = filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    mime_type = 'application/pdf'
                elif ext in ['doc', 'docx']:
                    mime_type = 'application/msword'
                elif ext in ['txt', 'md']:
                    mime_type = 'text/plain'
                else:
                    mime_type = 'application/octet-stream'

                files = {'file': (filename, f, mime_type)}
                payload = {
                    'title': title or filename, 
                    'description': description,
                    'document_id': new_doc.id
                }
                
                print(f"📤 Enviando a n8n (Intento de validación): {n8n_webhook}")
                response = requests.post(n8n_webhook, files=files, data=payload, timeout=60)
                
                if response.status_code == 200:
                    n8n_success = True
                else:
                    print(f"⚠️ n8n falló con código: {response.status_code}")

            # --- PASO 4: DECISIÓN FINAL ---
            if n8n_success:
                db.session.commit()
                flash("Documento procesado correctamente por la IA y guardado.", "success")
            else:
                raise Exception(f"n8n rechazó el documento (Status {response.status_code}). No se guardó nada.")

            return redirect(url_for("document.index"))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error crítico en creación: {e}")
            
            if save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    print("🧹 Archivo temporal eliminado tras fallo.")
                except:
                    pass

            flash(f"No se pudo crear el documento. Volver a intentar más tarde.", "danger")
            return redirect(url_for("document.create"))

    return redirect(url_for("document.create"))


@document_blueprint.post("/delete/<int:id>")
@login_required
def delete(id):
    # 1. Buscar el documento
    doc = db.session.query(Document).get(id)
    
    if not doc:
        flash("El documento no existe.", "danger")
        return redirect(url_for("document.index"))

    n8n_delete_webhook = "http://localhost:5678/webhook-test/delete-document"
    
    try:
        # --- PASO 1: ENVIAR A N8N PRIMERO ---
        print(f"📤 Solicitando eliminación a n8n primero...")
        payload = {"document_id": doc.id}
        
        response = requests.post(n8n_delete_webhook, json=payload, timeout=10)
        
        # --- PASO 2: VERIFICAR RESPUESTA DE N8N ---
        if response.status_code == 200:
            print("✅ n8n confirmó eliminación. Procediendo a borrar localmente.")
            
            # Borrar archivo físico
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except OSError as e:
                     print(f"⚠️ Advertencia: No se pudo borrar el archivo físico: {e}")
            
            # Borrar de BD
            db.session.delete(doc)
            db.session.commit()
            
            flash("Documento eliminado correctamente de la IA y del sistema.", "success")
        else:
            print(f"⚠️ n8n falló (Status {response.status_code}). Abortando eliminación local.")
            flash(f"No se pudo eliminar. Volver a intentar más tarde.", "warning")
            
    except Exception as e:
        print(f"❌ Error de conexión con n8n: {e}")
        flash("Error de conexión con la IA. Intenta más tarde. El documento no se eliminó.", "danger")

    return redirect(url_for("document.index"))