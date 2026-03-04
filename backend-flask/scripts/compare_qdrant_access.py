#!/usr/bin/env python3
"""
Script para verificar cómo Langchain ve los datos en Qdrant
y comparar con el cliente nativo de Qdrant
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def compare_qdrant_access():
    """Compara cómo diferentes clientes acceden a Qdrant"""
    try:
        print("\n" + "="*80)
        print("🔗 COMPARACIÓN: Cliente Nativo vs Langchain")
        print("="*80)
        
        # 1. ACCESO DIRECTO CON QDRANT CLIENT
        print("\n1️⃣  ACCESO DIRECTO (QdrantClient)")
        print("-" * 80)
        
        from qdrant_client import QdrantClient
        
        client = QdrantClient(url="http://localhost:6333")
        results_direct = client.scroll(
            collection_name="docs",
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        if results_direct[0]:
            point = results_direct[0][0]
            payload = point.payload
            
            print(f"✅ Conexión exitosa")
            print(f"\nEstructura obtenida:")
            print(f"  - Tipo payload: {type(payload)}")
            print(f"  - Claves en payload: {list(payload.keys())}")
            
            page_content = payload.get('pageContent', '')
            print(f"\n  - pageContent presente: {'✅' if 'pageContent' in payload else '❌'}")
            print(f"  - pageContent vacío: {'❌' if len(page_content) > 0 else '✅ (VACÍO)'}")
            print(f"  - Tamaño pageContent: {len(page_content)} caracteres")
            
            if page_content:
                print(f"  - Preview: {page_content[:80]}...")
        
        # 2. ACCESO CON LANGCHAIN
        print("\n\n2️⃣  ACCESO CON LANGCHAIN VectorStore")
        print("-" * 80)
        
        try:
            from langchain_qdrant import QdrantVectorStore
            from langchain_huggingface.embeddings import HuggingFaceEmbeddings
            
            print("✅ Langchain importado correctamente")
            
            # Crear embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="intfloat/multilingual-e5-large"
            )
            print("✅ Embeddings configurados")
            
            # Crear vector store
            vector_store = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                collection_name="docs",
                url="http://localhost:6333"
            )
            print("✅ Vector store conectado")
            
            # Realizar búsqueda
            docs = vector_store.similarity_search("Sistema Operativo", k=1)
            
            if docs:
                doc = docs[0]
                print(f"\n✅ Búsqueda exitosa")
                print(f"\nEstructura obtenida por Langchain:")
                print(f"  - Tipo: {type(doc)}")
                print(f"  - page_content presente: {'✅' if doc.page_content else '❌'}")
                print(f"  - page_content vacío: {'❌' if len(doc.page_content) > 0 else '✅ (VACÍO)'}")
                print(f"  - Tamaño page_content: {len(doc.page_content)} caracteres")
                
                if doc.page_content:
                    print(f"  - Preview: {doc.page_content[:80]}...")
                
                print(f"\n  - Metadata: {doc.metadata}")
            else:
                print(f"❌ Búsqueda no retornó documentos")
        
        except ImportError as e:
            print(f"⚠️  No se puede importar Langchain: {e}")
            print(f"    (Langchain puede no estar instalado)")
        except Exception as e:
            print(f"❌ Error con Langchain: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 COMPARACIÓN CLIENT NATIVO vs LANGCHAIN\n")
    compare_qdrant_access()
