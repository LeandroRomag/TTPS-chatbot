from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import os

class QdrantService:
    """Servicio para interactuar con Qdrant"""
    
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=self.url)
        self.collection_name = "docs"
        
        # Asegurar que la colección existe
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Crea la colección si no existe"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                print(f"📦 Creando colección '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1024,  # multilingual-e5-large tiene dimensión 1024
                        distance=Distance.COSINE
                    )
                )
                print(f"✅ Colección '{self.collection_name}' creada")
            else:
                print(f"✅ Colección '{self.collection_name}' ya existe")
                
        except Exception as e:
            print(f"⚠️ Error verificando colección: {e}")
    
    def insert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]], batch_size: int = 100) -> bool:
        """
        Inserta chunks con sus embeddings en Qdrant
        """
        try:
            if len(chunks) != len(embeddings):
                raise ValueError(f"Número de chunks ({len(chunks)}) no coincide con embeddings ({len(embeddings)})")
        
            # Preparar puntos
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                # MÚLTIPLES ALIAS para compatibilidad con n8n/LangChain
                content = chunk.get('pageContent', chunk.get('text', ''))
            
                payload = {
                    'pageContent': content,  # Para n8n/LangChain
                    'content': content,       #  adicional
                    'text': content,          #  adicional
                    'metadata': chunk['metadata']
                }
            
                # Validación
                if not content or len(content.strip()) < 10:
                    print(f"⚠️ Advertencia: chunk {chunk['id']} tiene contenido vacío o muy corto")
                    continue  # Saltar chunks vacíos
            
                points.append(
                    PointStruct(
                        id=chunk['id'],
                        vector=embedding,
                        payload=payload
                    )
                )
        
            if not points:
                print("❌ No hay puntos válidos para insertar")
                return False
        
            # Insertar en batches
            total_inserted = 0
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
            
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
                total_inserted += len(batch)
                print(f"✅ Insertados {total_inserted}/{len(points)} puntos")
        
            print(f"🎉 Todos los {len(points)} puntos insertados exitosamente")
            return True
        
        except Exception as e:
            print(f"❌ Error insertando en Qdrant: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_by_document_id(self, document_id: int) -> bool:
        """Elimina todos los chunks de un documento"""
        try:
            print(f"🗑️ Eliminando chunks del documento {document_id} de Qdrant...")
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.document_id",  
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            
            print(f"✅ Chunks del documento {document_id} eliminados de Qdrant")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando de Qdrant: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_chunks_by_document(self, document_id: int, limit: int = 100) -> List[Dict]:
        """Obtiene todos los chunks de un documento"""
        try:
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.document_id",  
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            chunks = []
            for point in results[0]:
                # Mantener estructura con pageContent y metadata
                chunks.append({
                    'id': point.id,
                    'payload': {
                        'pageContent': point.payload.get('pageContent', ''),
                        **point.payload.get('metadata', {})
                    }
                })
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error obteniendo chunks: {e}")
            return []
    
    def search_similar(self, query_vector: List[float], limit: int = 5, document_id: int = None) -> List[Dict]:
        """Busca chunks similares usando el índice HNSW nativo de Qdrant"""
        try:
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            ).points

            return [
                {
                    'id': point.id,
                    'score': point.score,
                    'payload': {
                        'pageContent': point.payload.get('pageContent', ''),
                        **point.payload.get('metadata', {})
                    }
                }
                for point in results
            ]

        except Exception as e:
            print(f"❌ Error buscando en Qdrant: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_sample_payloads(self, document_id: int = None, limit: int = 5) -> List[Dict]:
        """
        Obtiene una muestra de payloads para debug
        """
        try:
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.document_id", 
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            samples = []
            for point in results[0]:
                # Truncar pageContent
                page_content = point.payload.get('pageContent', '')
                truncated = page_content[:250] + "..." if len(page_content) > 250 else page_content
                
                samples.append({
                    'id': point.id,
                    'payload': {
                        'pageContent': truncated,
                        'metadata': point.payload.get('metadata', {})
                    }
                })
            
            return samples
            
        except Exception as e:
            print(f"❌ Error obteniendo samples: {e}")
            import traceback
            traceback.print_exc()
            return []