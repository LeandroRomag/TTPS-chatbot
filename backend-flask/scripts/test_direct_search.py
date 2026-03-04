#!/usr/bin/env python
"""
Búsqueda directa en Qdrant sin servicios
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.utils.embeddings import EmbeddingService
import os

def test_direct_search():
    query = "evaluacion parciales examenes"
    
    print(f"🔍 Buscando: '{query}'\n")
    
    # 1. Generar embedding
    print("1️⃣ Generando embedding...")
    embedding_service = EmbeddingService()
    query_embedding = embedding_service.get_embedding(query)
    print(f"✅ Embedding generado (dim: {len(query_embedding)})")
    
    # 2. Conectar a Qdrant directamente
    print("\n2️⃣ Buscando en Qdrant...")
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    
    # Filtro por documento
    query_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.document_id",
                match=MatchValue(value=30)
            )
        ]
    )
    
    # Buscar usando el método correcto
    try:
        # OPCIÓN 1: Método moderno
        from qdrant_client.models import SearchRequest
        
        results = client.search_batch(
            collection_name="docs",
            requests=[
                SearchRequest(
                    vector=query_embedding,
                    filter=query_filter,
                    limit=10,
                    with_payload=True
                )
            ]
        )
        
        hits = results[0] if results else []
        
    except Exception as e:
        print(f"⚠️ search_batch falló: {e}")
        print("Intentando con scroll + comparación manual...")
        
        # OPCIÓN 2: Método de respaldo - traer todos y ordenar manualmente
        all_points = []
        offset = None
        
        while True:
            result = client.scroll(
                collection_name="docs",
                scroll_filter=query_filter,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            points, offset = result
            if not points:
                break
            all_points.extend(points)
            if offset is None:
                break
        
        # Calcular similitud coseno manualmente
        import numpy as np
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        query_vec = np.array(query_embedding)
        
        hits = []
        for point in all_points:
            point_vec = np.array(point.vector)
            score = cosine_similarity(query_vec, point_vec)
            
            # Crear objeto similar a hit
            class Hit:
                def __init__(self, id, score, payload):
                    self.id = id
                    self.score = score
                    self.payload = payload
            
            hits.append(Hit(point.id, float(score), point.payload))
        
        # Ordenar por score descendente
        hits.sort(key=lambda x: x.score, reverse=True)
        hits = hits[:10]
    
    print(f"✅ Encontrados {len(hits)} resultados\n")
    
    # 3. Mostrar top 5
    print("📊 TOP 5 RESULTADOS:\n")
    for i, hit in enumerate(hits[:5], 1):
        payload = hit.payload
        metadata = payload.get('metadata', {})
        
        score = hit.score
        section = metadata.get('section_title', 'Sin título')
        hierarchy = metadata.get('section_hierarchy', '')
        chunk_idx = metadata.get('chunk_index', '?')
        content = payload.get('pageContent', '')[:200]
        
        print(f"{i}. Score: {score:.4f}")
        print(f"   Sección: {section}")
        print(f"   Jerarquía: {hierarchy}")
        print(f"   Chunk: {chunk_idx}")
        print(f"   Content: {content}...")
        print()

if __name__ == "__main__":
    test_direct_search()