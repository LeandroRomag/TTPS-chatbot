from pydoc import text
from sys import prefix

import requests
import os
from typing import List
import numpy as np

class EmbeddingService:
    """Servicio para generar embeddings usando HuggingFace API con fallback a local"""
    
    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_API_TOKEN")
        self.model = "intfloat/multilingual-e5-large"
        self.api_url = f"https://router.huggingface.co/models/{self.model}"
        self.local_service = None
        
        if not self.hf_token:
            print("⚠️  HUGGINGFACE_API_TOKEN no está configurado, usando embeddings locales")
            self._init_local_service()
    
    def _init_local_service(self):
        """Inicializa el servicio de embeddings local como fallback"""
        try:
            self.local_service = LocalEmbeddingService()
        except Exception as e:
            raise ValueError(f"No se puede inicializar ni API remota ni local: {str(e)}")
    
    def get_embeddings(self, texts: List[str], batch_size: int = 10, prefix: str = "") -> List[List[float]]:
        """
        Obtiene embeddings para una lista de textos
        
        Args:
            texts: Lista de textos a embedear
            batch_size: Tamaño del batch para la API
            
        Returns:
            Lista de embeddings (vectores)
        """
        # Si no hay token, usar servicio local
        if prefix:
            texts = [f"{prefix}{t}" for t in texts]
        if not self.hf_token:
            return self.local_service.get_embeddings(texts, batch_size=32)
        
        all_embeddings = []
        
        # Procesar en batches para no sobrecargar la API
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"🔄 Procesando batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.hf_token}"},
                    json={"inputs": batch},
                    timeout=120
                )
                
                if response.status_code != 200:
                    error_text = response.text[:200] if response.text else "Empty response"
                    print(f"❌ API error ({response.status_code}): {error_text}")
                    print("🔄 Cambiando a embeddings locales...")
                    self._init_local_service()
                    return self.local_service.get_embeddings(texts, batch_size=32)
                
                batch_embeddings = response.json()
                
                # Si es un solo texto, viene como array directo, si son múltiples como array de arrays
                if isinstance(batch_embeddings[0], (int, float)):
                    all_embeddings.append(batch_embeddings)
                else:
                    all_embeddings.extend(batch_embeddings)
                
            except (requests.exceptions.RequestException, ValueError) as e:
                print(f"⚠️  Error con API remota: {str(e)}")
                print("🔄 Cambiando a embeddings locales...")
                self._init_local_service()
                return self.local_service.get_embeddings(texts, batch_size=32)
        
        return all_embeddings
    
    def get_embedding(self, text: str, prefix: str = "") -> List[float]:
        return self.get_embeddings([text], prefix=prefix)[0]


# Opción alternativa: Usar modelo local (más rápido pero requiere más recursos)
class LocalEmbeddingService:
    """Servicio para generar embeddings localmente con sentence-transformers"""
    
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        print("📥 Cargando modelo de embeddings localmente...")
        self.model = SentenceTransformer('intfloat/multilingual-e5-large')
        print("✅ Modelo cargado")
    
    def get_embeddings(self, texts: List[str], batch_size: int = 32, prefix: str = "") -> List[List[float]]:
        if prefix:
            texts = [f"{prefix}{t}" for t in texts]
        print(f"🔄 Generando embeddings para {len(texts)} textos...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def get_embedding(self, text: str, prefix: str = "") -> List[float]:
        return self.get_embeddings([text], prefix=prefix)[0]