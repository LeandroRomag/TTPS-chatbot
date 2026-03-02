#!/usr/bin/env python
"""
Verifica la estructura de los datos en Qdrant
"""

from qdrant_client import QdrantClient
import os

def verify_structure():
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    
    print("🔍 Verificando estructura de Qdrant...\n")
    
    # Obtener algunos puntos
    results = client.scroll(
        collection_name="docs",
        limit=3,
        with_payload=True,
        with_vectors=False
    )
    
    if not results[0]:
        print("❌ No hay puntos en la colección")
        return
    
    print(f"✅ Encontrados {len(results[0])} puntos\n")
    
    for i, point in enumerate(results[0], 1):
        print(f"{'='*60}")
        print(f"PUNTO {i}")
        print(f"{'='*60}")
        print(f"ID: {point.id}")
        
        payload = point.payload
        
        # Verificar campos críticos
        has_pageContent = 'pageContent' in payload
        has_text = 'text' in payload
        
        print(f"\n📋 Campos presentes:")
        print(f"  - pageContent: {'✅' if has_pageContent else '❌'}")
        print(f"  - text: {'✅' if has_text else '❌'}")
        print(f"  - section_title: {'✅' if 'section_title' in payload else '❌'}")
        print(f"  - document_id: {'✅' if 'document_id' in payload else '❌'}")
        print(f"  - filename: {'✅' if 'filename' in payload else '❌'}")
        
        # Mostrar estructura completa del primer punto
        if i == 1:
            print(f"\n📦 Estructura completa del payload:")
            for key in sorted(payload.keys()):
                value = payload[key]
                if key in ['pageContent', 'text'] and isinstance(value, str) and len(value) > 100:
                    print(f"  - {key}: '{value[:100]}...' (length: {len(value)})")
                elif isinstance(value, list):
                    print(f"  - {key}: {value} (list, length: {len(value)})")
                else:
                    print(f"  - {key}: {value}")
        
        # Validar contenido
        if has_pageContent:
            content = payload['pageContent']
            is_empty = not content or not content.strip()
            print(f"\n📝 Contenido pageContent:")
            print(f"  - Vacío: {'❌ SÍ' if is_empty else '✅ NO'}")
            print(f"  - Longitud: {len(content) if content else 0}")
            if not is_empty and content:
                print(f"  - Preview: '{content[:150]}...'")
        else:
            print(f"\n⚠️ PROBLEMA: Este punto NO tiene pageContent")
        
        print()
    
    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}")
    
    # Contar cuántos tienen pageContent
    all_points = []
    offset = None
    while True:
        result = client.scroll(
            collection_name="docs",
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        points, offset = result
        if not points:
            break
        all_points.extend(points)
        if offset is None:
            break
    
    total = len(all_points)
    with_pageContent = sum(1 for p in all_points if 'pageContent' in p.payload)
    empty_pageContent = sum(1 for p in all_points if 'pageContent' in p.payload and not p.payload['pageContent'].strip())
    
    print(f"Total de puntos: {total}")
    print(f"Con pageContent: {with_pageContent} ({with_pageContent/total*100:.1f}%)")
    print(f"pageContent vacío: {empty_pageContent} ({empty_pageContent/total*100:.1f}%)")
    
    if with_pageContent < total:
        print(f"\n⚠️ ADVERTENCIA: {total - with_pageContent} puntos sin pageContent")
    
    if empty_pageContent > 0:
        print(f"\n⚠️ ADVERTENCIA: {empty_pageContent} puntos con pageContent vacío")

if __name__ == "__main__":
    verify_structure()