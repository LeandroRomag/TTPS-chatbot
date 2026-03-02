from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from src.core.board.document import Document
from src.core.database import db
from src.web.controllers.auth_controller import login_required 
from src.utils.pdf_chunker import process_pdf_file
from src.utils.embeddings import EmbeddingService  
from src.utils.qdrant_service import QdrantService  
import os
import hashlib
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_stream):
    """Calcula el hash SHA256 de un archivo para verificar duplicados por contenido."""
    sha256_hash = hashlib.sha256()
    for byte_block in iter(lambda: file_stream.read(4096), b""):
        sha256_hash.update(byte_block)
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
        # --- VALIDACIÓN: VERIFICAR DUPLICADO POR CONTENIDO (HASH) ---
        try:
            incoming_hash = calculate_file_hash(file)
            existing_docs = db.session.query(Document).all()
            
            for doc in existing_docs:
                if doc.file_path and os.path.exists(doc.file_path):
                    with open(doc.file_path, 'rb') as f_existing:
                        existing_hash = calculate_file_hash(f_existing)
                        
                        if incoming_hash == existing_hash:
                            flash(f"Este archivo ya existe en el sistema (Documento: '{doc.title}'). No se permite subir duplicados.", "warning")
                            return redirect(url_for("document.create"))
        except Exception as e:
            print(f"Error verificando duplicados: {e}")

        save_path = None
        try:
            # --- PASO 1: GUARDAR ARCHIVO FÍSICO ---
            filename = secure_filename(file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            
            if os.path.exists(save_path):
                base, ext = os.path.splitext(filename)
                import uuid
                filename = f"{base}_{uuid.uuid4().hex[:6]}{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)

            file.save(save_path)
            print(f"💾 Archivo guardado: {save_path}")

            # --- PASO 2: PREPARAR BASE DE DATOS (SIN COMMIT) ---
            new_doc = Document(
                title=title,
                description=description,
                file_path=save_path,
                uploaded_by=session["user_id"] 
            )
            db.session.add(new_doc)
            db.session.flush()
            print(f"📝 Documento preparado en BD (ID: {new_doc.id})")

            # --- PASO 3: PROCESAR PDF Y GENERAR EMBEDDINGS ---
            ext = filename.rsplit('.', 1)[1].lower()
            
            if ext == 'pdf':
                print(f"📄 Procesando PDF con chunking estructurado...")
                
                try:
                    # 3.1 Generar chunks por secciones
                    chunks = process_pdf_file(
                        save_path,
                        metadata={
                            'document_id': new_doc.id,
                            'title': title or filename,
                            'description': description,
                            'uploaded_by': session["user_id"],
                            'filename': filename
                        }
                    )
                    print(f"✅ Generados {len(chunks)} chunks estructurados")
                    
                    # 3.2 Generar embeddings
                    print(f"🔄 Generando embeddings...")
                    embedding_service = EmbeddingService()
                    texts = [chunk['text'] for chunk in chunks]
                    embeddings = embedding_service.get_embeddings(texts, batch_size=10, prefix="passage: ")
                    print(f"✅ Embeddings generados")
                    
                    # 3.3 Insertar en Qdrant
                    print(f"📤 Insertando en Qdrant...")
                    qdrant_service = QdrantService()
                    success = qdrant_service.insert_chunks(chunks, embeddings, batch_size=100)
                    
                    if not success:
                        raise Exception("Error insertando chunks en Qdrant")
                    
                    # 3.4 Todo OK - commit
                    db.session.commit()
                    flash(f"✅ Documento procesado correctamente. Se generaron {len(chunks)} secciones.", "success")
                    print(f"🎉 Documento {new_doc.id} procesado completamente")
                    
                except Exception as e:
                    print(f"❌ Error procesando PDF: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Rollback DB
                    db.session.rollback()
                    
                    # Limpiar archivo
                    if save_path and os.path.exists(save_path):
                        os.remove(save_path)
                        print("🧹 Archivo temporal eliminado")
                    
                    flash(f"Error procesando el documento: {str(e)}", "danger")
                    return redirect(url_for("document.create"))
            
            else:
                # Para otros formatos, por ahora solo guardar en BD
                db.session.commit()
                flash("Documento guardado. (Procesamiento de embeddings solo disponible para PDF)", "info")

            return redirect(url_for("document.index"))

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error crítico: {e}")
            import traceback
            traceback.print_exc()
            
            if save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except:
                    pass

            flash(f"Error creando documento: {str(e)}", "danger")
            return redirect(url_for("document.create"))

    return redirect(url_for("document.create"))


@document_blueprint.post("/delete/<int:id>")
@login_required
def delete(id):
    """Eliminar documento de BD y Qdrant"""
    doc = db.session.query(Document).get(id)
    
    if not doc:
        flash("El documento no existe.", "danger")
        return redirect(url_for("document.index"))

    try:
        print(f"🗑️ Eliminando documento {id}...")
        
        # 1. Eliminar de Qdrant primero
        qdrant_service = QdrantService()
        qdrant_success = qdrant_service.delete_by_document_id(doc.id)
        
        if not qdrant_success:
            print("⚠️ Error eliminando de Qdrant, pero continuando...")
        
        # 2. Eliminar archivo físico
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
                print(f"✅ Archivo físico eliminado: {doc.file_path}")
            except OSError as e:
                print(f"⚠️ No se pudo borrar archivo: {e}")
        
        # 3. Eliminar de BD
        db.session.delete(doc)
        db.session.commit()
        
        flash("Documento eliminado correctamente del sistema y de la IA.", "success")
        print(f"✅ Documento {id} eliminado completamente")
        
    except Exception as e:
        print(f"❌ Error eliminando documento: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        flash("Error eliminando el documento. Intenta más tarde.", "danger")

    return redirect(url_for("document.index"))


@document_blueprint.get("/<int:id>/chunks")
@login_required
def view_chunks(id):
    """Ver los chunks/secciones de un documento procesado"""
    doc = db.session.query(Document).get(id)
    
    if not doc:
        flash("El documento no existe.", "danger")
        return redirect(url_for("document.index"))
    
    try:
        qdrant_service = QdrantService()
        chunks = qdrant_service.get_chunks_by_document(doc.id, limit=200)
        
        chunks_data = []
        for chunk in chunks:
            payload = chunk['payload']
            chunks_data.append({
                'section_title': payload.get('section_title', 'Sin título'),
                'section_hierarchy': payload.get('section_hierarchy', ''),
                'section_level': payload.get('section_level', 0),
                'chunk_length': payload.get('chunk_length', 0),
                'chunk_index': payload.get('chunk_index', 0),
                'text_preview': payload.get('text', '')[:200] + '...'
            })
        
        # Ordenar por chunk_index
        chunks_data.sort(key=lambda x: x['chunk_index'])
        
        return render_template(
            "document/chunks.html", 
            document=doc, 
            chunks=chunks_data,
            active_page='documentos'
        )
        
    except Exception as e:
        print(f"Error obteniendo chunks: {e}")
        import traceback
        traceback.print_exc()
        flash("No se pudieron cargar los chunks del documento.", "warning")
        return redirect(url_for("document.index"))
@document_blueprint.get("/api/list", strict_slashes=False)
def api_list_documents():
    """
    Endpoint para n8n: devuelve la lista de documentos en JSON
    Uso: GET /document/api/list
    Respuesta: {"documentos": [{"id": 1, "nombre": "...", "descripcion": "...", "created_at": "...", "filepath": "..."}]}
    """
    try:
        docs = db.session.query(Document).order_by(Document.uploaded_at.desc()).all()
        
        documentos = []
        for doc in docs:
            documentos.append({
                "id": doc.id,
                "nombre": doc.title,
                "descripcion": doc.description,
                "filepath": doc.file_path,
                "created_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "uploaded_by": doc.uploaded_by,
                
            })
        
        return {
            "total": len(documentos),
            "documentos": documentos
        }, 200
        
    except Exception as e:
        print(f"Error en api_list_documents: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500

@document_blueprint.post("/api/search", strict_slashes=False)
def api_search_chunks():
    """
    Endpoint para n8n: busca chunks en Qdrant con filtro opcional por documento
    
    Uso: POST /document/api/search
    Body JSON:
    {
        "query": "texto a buscar",
        "document_id": 19  // OPCIONAL: filtrar por documento específico
    }
    
    Respuesta: 
    {
        "resultados": [
            {
                "score": 0.92,
                "texto": "...",
                "seccion": "...",
                "document_id": 19,
                "chunk_index": 5
            }
        ]
    }
    """
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        document_id = data.get("document_id")  # Opcional
        
        if not query:
            return {"error": "Query vacía"}, 400
        
        # 1. Generar embedding de la query
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.get_embedding(query, prefix="query: ")
        
        # 2. Buscar en Qdrant (con filtro de document_id si se proporciona)
        qdrant_service = QdrantService()
        resultados_qdrant = qdrant_service.search_similar(
            query_vector=query_embedding,
            limit=10,
            document_id=document_id  # Pasa None si no se especifica
        )
        
        # 3. Formatear respuesta
        resultados = []
        for hit in resultados_qdrant:
            payload = hit['payload']
            # ✅ CORREGIDO: Usar 'pageContent' en lugar de 'text'
            page_content = payload.get('pageContent', '')
            texto_preview = page_content[:300] + "..." if len(page_content) > 300 else page_content
            
            resultados.append({
                "score": round(hit['score'], 3),
                "texto": texto_preview,
                "seccion": payload.get('section_title', 'Sin título'),
                "jerarquia": payload.get('section_hierarchy', ''),
                "document_id": payload.get('document_id'),
                "chunk_index": payload.get('chunk_index'),
                "archivo": payload.get('filename', 'Desconocido')
            })
        
        return {
            "query": query,
            "filtro_document_id": document_id,
            "total_resultados": len(resultados),
            "resultados": resultados
        }, 200
        
    except Exception as e:
        print(f"Error en api_search_chunks: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500
