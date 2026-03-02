import pymupdf4llm
import json
from datetime import datetime
from pathlib import Path
import hashlib
import re

class PDFChunker:
    def __init__(self, max_chunk_size=1500, overlap=200):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def process_pdf(self, pdf_path, metadata=None):
        """Procesa un PDF y retorna chunks listos para Qdrant"""
        
        print(f"📄 Convirtiendo {pdf_path} a Markdown...")
        try:
            md_text = pymupdf4llm.to_markdown(pdf_path)
        except Exception as e:
            print(f"❌ Error al convertir PDF: {e}")
            raise
        
        # Guardar markdown para debug (opcional)
        debug_folder = Path(pdf_path).parent / 'debug'
        debug_folder.mkdir(exist_ok=True)
        md_file = debug_folder / f"{Path(pdf_path).stem}_debug.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        print(f"✓ Markdown guardado en {md_file}")
        
        print("✂️  Dividiendo por secciones...")
        chunks = self._split_by_sections(md_text)
        
        print(f"📦 Preparando {len(chunks)} chunks...")
        documents = self._prepare_for_qdrant(chunks, pdf_path, metadata)
        
        return documents
    
    def _is_footer(self, title: str) -> bool:
        """True si el texto parece un pie de página (dirección, teléfono, web), no un título de sección."""
        if not title or len(title) > 120:
            return True
        t = title.lower().strip()
        # Patrones típicos de footers
        if re.search(r'\btel\.?\s*[:\(]|\bwww\.|\.(com|edu|ar)\b', t):
            return True
        if re.search(r'\bc\.?\s*p\.?\s*\d+|calle\s+\d+|república\s+argentina', t):
            return True
        if '|' in t and (re.search(r'\d{4,}', t) or 'la plata' in t or 'c.p.' in t):
            return True
        return False

    def _is_all_caps_heading(self, title: str) -> bool:
        """Heurística: título en MAYÚSCULAS (ignora dígitos/signos)."""
        letters = [c for c in (title or "") if c.isalpha()]
        if len(letters) < 4:
            return False
        return all(c == c.upper() for c in letters)

    def _looks_like_numbered_subheading(self, title: str) -> bool:
        """Ej: '1) Introducción', '2) Procesos y Scheduling', 'III) ...'."""
        if not title:
            return False
        return bool(
            re.match(r'^\s*\d+\)\s+\S', title)
            or re.match(r'^\s*\d+\.\s+\S', title)
            or re.match(r'^\s*[IVXLCDM]+\)\s+\S', title)
        )

    def _extract_full_emphasis_title(self, line: str) -> str | None:
        """
        Extrae el texto si la línea es *solo* un título con énfasis completo.
        Acepta:
        - **TÍTULO**
        - __TÍTULO__
        - _**TÍTULO**_ (italics+bold, como en tu debug)
        - _ __TÍTULO__ _
        """
        if line is None:
            return None
        s = line.strip()
        # _**T**_ o **T**
        m = re.match(r'^\s*_?\s*\*\*(.+?)\*\*\s*_?\s*$', s)
        if m:
            return m.group(1).strip()
        # _ __T__ _ o __T__
        m = re.match(r'^\s*_?\s*__(.+?)__\s*_?\s*$', s)
        if m:
            return m.group(1).strip()
        return None

    def _parse_header(self, line):
        """
        Detecta si la línea es un encabezado. Retorna (True, level, title) o (False, None, None).
        - # ## ### → level 1, 2, 3...
        - Línea SOLO con énfasis completo (**TÍTULO** o _**TÍTULO**_):
          - Si está en MAYÚSCULAS → sección principal (level 1)
          - Si parece numerada (1), 2), III)...) → subsección (level 2)
          - Si parece footer (tel/web/dirección) → se ignora
        """
        # Encabezados markdown (# ## ###) siempre se aceptan
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            return True, len(m.group(1)), m.group(2).strip()
        title = self._extract_full_emphasis_title(line)
        if title is not None:
            if self._is_footer(title):
                return False, None, None
            clean = re.sub(r'</?u>', '', title).strip()
            if self._is_all_caps_heading(clean):
                return True, 1, clean
            if self._looks_like_numbered_subheading(clean):
                return True, 2, clean
            # Si no es MAYÚSCULAS ni numerada, por defecto no lo tomamos como header
            # (evita cosas como 'Año 2025' u otros resaltados sueltos)
            return False, None, None
        return False, None, None

    def _split_by_sections(self, md_text):
        """Divide el markdown por encabezados (# y líneas solo en negrita)"""
        lines = md_text.split('\n')
        chunks = []
        current_chunk = {
            'title': 'Sin sección',
            'level': 0,
            'content': [],
            'hierarchy': []
        }
        
        title_stack = []
        
        for line in lines:
            is_header, level, title = self._parse_header(line)
            
            if is_header:
                # Guardar chunk anterior si tiene contenido
                if current_chunk['content']:
                    content = '\n'.join(current_chunk['content']).strip()
                    
                    if content:  # Solo si hay contenido real
                        # Dividir si es muy grande
                        if len(content) > self.max_chunk_size:
                            sub_chunks = self._split_large_content(
                                content,
                                current_chunk['title'],
                                current_chunk['hierarchy']
                            )
                            chunks.extend(sub_chunks)
                        else:
                            current_chunk['content'] = content
                            chunks.append(current_chunk.copy())
                
                # Actualizar jerarquía: truncar a nivel-1 y anexar título actual
                # level es 1-based (1=sección principal, 2=subsección, etc.)
                title_stack = title_stack[: max(level - 1, 0)]
                title_stack.append(title)

                current_chunk = {
                    'title': title,
                    'level': level,
                    'content': [line],
                    'hierarchy': [t for t in title_stack if t]
                }
            else:
                current_chunk['content'].append(line)
        
        # Último chunk
        if current_chunk['content']:
            content = '\n'.join(current_chunk['content']).strip()
            if content:
                if len(content) > self.max_chunk_size:
                    sub_chunks = self._split_large_content(
                        content,
                        current_chunk['title'],
                        current_chunk['hierarchy']
                    )
                    chunks.extend(sub_chunks)
                else:
                    current_chunk['content'] = content
                    chunks.append(current_chunk)
        
        return chunks
    
    def _split_large_content(self, content, title, hierarchy):
        """Divide contenido grande manteniendo el contexto"""
        chunks = []
        
        # Intentar dividir por párrafos
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        current = []
        current_size = 0
        part = 1
        
        for para in paragraphs:
            para_size = len(para)
            
            if current_size + para_size > self.max_chunk_size and current:
                # Guardar chunk actual
                chunks.append({
                    'title': f"{title} (parte {part})",
                    'level': len(hierarchy),
                    'content': '\n\n'.join(current),
                    'hierarchy': hierarchy + [f"parte {part}"]
                })
                
                # Overlap: mantener último párrafo
                if self.overlap > 0 and current:
                    current = [current[-1], para]
                    current_size = len(current[-1]) + para_size
                else:
                    current = [para]
                    current_size = para_size
                
                part += 1
            else:
                current.append(para)
                current_size += para_size
        
        # Último chunk
        if current:
            chunks.append({
                'title': f"{title} (parte {part})" if part > 1 else title,
                'level': len(hierarchy),
                'content': '\n\n'.join(current),
                'hierarchy': hierarchy + ([f"parte {part}"] if part > 1 else [])
            })
        
        return chunks
    
    def _prepare_for_qdrant(self, chunks, pdf_path, custom_metadata=None):
        """Prepara chunks para insertar en Qdrant con formato compatible con n8n"""
        documents = []
        filename = Path(pdf_path).name
        
        for i, chunk in enumerate(chunks):
            # Crear ID único
            chunk_id = hashlib.md5(
                f"{filename}_{i}_{chunk['title']}".encode()
            ).hexdigest()
            
            #  ESTRUCTURA CORRECTA: pageContent en nivel superior, metadata anidado
            doc = {
                'id': chunk_id,
                'text': chunk['content'], 
                'pageContent': chunk['content'],  
                'metadata': {
                    
                    'filename': filename,
                    'section_title': chunk['title'],
                    'section_level': chunk['level'],
                    'section_hierarchy': ' > '.join(chunk['hierarchy']),
                    'full_path': chunk['hierarchy'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'has_identified_section': True,
                    'ingesta': datetime.now().isoformat(),
                    'chunk_length': len(chunk['content']),
                    **(custom_metadata or {})
                }
            }
            
            documents.append(doc)
        
        return documents


# Función principal para usar desde Flask
def process_pdf_file(pdf_path, metadata=None):
    """Función principal para procesar un PDF"""
    chunker = PDFChunker(max_chunk_size=1500, overlap=200)
    documents = chunker.process_pdf(pdf_path, metadata)
    return documents