"""RAG utilities: extracción de texto de PDFs, chunking, almacenamiento SQLite y recuperación BM25.

Funciones principales usadas por la app:
- add_pdf_file: sube e indexa un PDF
- retrieve_bm25: recupera chunks relevantes para una consulta
- make_context: construye el bloque de contexto con límites configurables
"""

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

DB_PATH = os.path.join("data", "docs.sqlite")


def _ensure_dirs():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db() -> None:
    """Crea tablas si no existen (documents, chunks)."""
    _ensure_dirs()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                title TEXT,
                uploaded_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        con.commit()


def _normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


# reset_index removido: ya no se expone endpoint para limpiar todo


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrae texto de un PDF (pypdf -> PyMuPDF -> OCR opcional).

    Devuelve string normalizado (espacios condensados) o "" si no se pudo extraer.
    """
    from io import BytesIO

    # Primer intento: pypdf
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts: List[str] = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        text = _normalize_ws("\n".join(parts))
        if text:
            return text
    except Exception:
        pass

    # Fallback: PyMuPDF (mejor en algunos PDFs)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        parts: List[str] = []
        for page in doc:
            try:
                parts.append(page.get_text("text") or "")
            except Exception:
                continue
        text = _normalize_ws("\n".join(parts))
        if text:
            return text
        # Intentar OCR si no hay texto (PDF escaneado)
        try:
            import pytesseract
            from PIL import Image
            parts = []
            for page in doc:
                try:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    txt = pytesseract.image_to_string(img, lang="spa+eng")
                    parts.append(txt or "")
                except Exception:
                    continue
            ocr_text = _normalize_ws("\n".join(parts))
            return ocr_text
        except Exception:
            return ""
    except Exception:
        return ""


def chunk_text(text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None) -> List[str]:
    """Divide el texto en trozos solapados para recuperación.
    Tamaños por env si no se pasan: RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP.
    """
    text = _normalize_ws(text)
    if not text:
        return []
    try:
        chunk_size = int(chunk_size) if chunk_size is not None else int(os.getenv("RAG_CHUNK_SIZE", "600"))
    except Exception:
        chunk_size = 600
    try:
        overlap = int(overlap) if overlap is not None else int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
    except Exception:
        overlap = 100
    chunk_size = max(50, chunk_size)
    overlap = max(0, min(overlap, chunk_size - 1))

    words = text.split(" ")
    chunks: List[str] = []
    i = 0
    step = max(1, chunk_size - overlap)
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_words))
        if i + chunk_size >= len(words):
            break
        i += step
    return chunks


def add_document_from_text(filename: str, text: str) -> int:
    """Inserta el documento y sus chunks en la BD. Devuelve document_id."""
    init_db()
    ts = datetime.utcnow().isoformat()
    chunks = chunk_text(text)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO documents (filename, title, uploaded_at) VALUES (?, ?, ?)",
            (filename, None, ts),
        )
        doc_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO chunks (document_id, chunk_index, text) VALUES (?, ?, ?)",
            [(doc_id, idx, c) for idx, c in enumerate(chunks)],
        )
        con.commit()
    return doc_id


def add_pdf_file(filename: str, file_bytes: bytes) -> Tuple[int, int]:
    """Indexa un PDF y devuelve (document_id, chunk_count)."""
    text = extract_text_from_pdf(file_bytes)
    doc_id = add_document_from_text(filename, text)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?", (doc_id,))
        n = int(cur.fetchone()[0])
    return doc_id, n


@dataclass
class RetrievedChunk:
    document_id: int
    chunk_index: int
    text: str
    score: float


def _load_all_chunks(doc_id: Optional[int] = None) -> List[Tuple[int, int, str]]:
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        if doc_id is None:
            cur.execute("SELECT document_id, chunk_index, text FROM chunks")
            rows = cur.fetchall()
        else:
            cur.execute("SELECT document_id, chunk_index, text FROM chunks WHERE document_id = ?", (int(doc_id),))
            rows = cur.fetchall()
    return [(int(r[0]), int(r[1]), str(r[2])) for r in rows]


"""Funciones de listado detallado removidas para simplificar (no usadas por la app)."""


"""Conteo de chunks removido (no usado por la app)."""


"""get_doc_chunks removido: modo full_doc no se usa actualmente por la app."""


def _tokenize(doc: str) -> List[str]:
    return re.findall(r"\w+", doc.lower())


def retrieve_bm25(query: str, top_k: int = 5, doc_id: Optional[int] = None) -> List[RetrievedChunk]:
    """Recupera top_k chunks usando BM25. Si doc_id se pasa, filtra por ese documento."""
    rows = _load_all_chunks(doc_id=doc_id)
    if not rows:
        return []
    corpus = [r[2] for r in rows]
    tokenized = [_tokenize(c) for c in corpus]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(_tokenize(query or ""))
    # Ordenar por score desc
    ranked = sorted(zip(range(len(rows)), scores), key=lambda x: x[1], reverse=True)[:top_k]
    out: List[RetrievedChunk] = []
    for idx, score in ranked:
        doc_id, chunk_idx, text = rows[idx]
        out.append(RetrievedChunk(document_id=doc_id, chunk_index=chunk_idx, text=text, score=float(score)))
    return out


def make_context(chunks: List[RetrievedChunk], max_chars: Optional[int] = None) -> str:
    """Crea un bloque de contexto concatenando chunks con un límite global y por chunk."""
    if max_chars is None:
        try:
            max_chars = int(os.getenv("RAG_CONTEXT_CHARS", "4000"))
        except Exception:
            max_chars = 4000
    parts: List[str] = []
    total = 0
    # Límite por chunk para evitar pegar trozos gigantes y mejorar latencia
    try:
        per_chunk_cap = int(os.getenv("RAG_PER_CHUNK_MAX_CHARS", "1200"))
    except Exception:
        per_chunk_cap = 1200

    for ch in chunks:
        s = (ch.text or "").strip()
        if not s:
            continue
        # Presupone ~50 caracteres de overhead por etiqueta
        overhead = 50
        budget = max_chars - total - overhead
        if budget <= 0:
            break
        # Aplica límite por chunk y por presupuesto global
        if per_chunk_cap > 0 and len(s) > per_chunk_cap:
            s = s[:per_chunk_cap]
        if len(s) > budget:
            s = s[:budget]
        parts.append(f"[doc={ch.document_id} chunk={ch.chunk_index}] {s}")
        total += len(s) + 1
    return "\n\n".join(parts)


"""Listado de documentos removido (no usado por la app)."""
