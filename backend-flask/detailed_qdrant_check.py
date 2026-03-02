#!/usr/bin/env python3
"""
Script detallado para verificar el estado de TODOS los documentos en Qdrant
Identifica cuáles tienen pageContent vacío y cuáles no
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def detailed_check():
    """Verifica TODOS los documentos en Qdrant"""
    try:
        from utils.qdrant_service import QdrantService
        
        print("\n" + "="*80)
        print("🔬 ANÁLISIS DETALLADO DE TODOS LOS DOCUMENTOS EN QDRANT")
        print("="*80)
        
        qdrant = QdrantService()
        
        # Obtener información de la colección
        info = qdrant.client.get_collection("docs")
        total_points = info.points_count
        
        print(f"\n📊 Total de puntos: {total_points}")
        
        # Scroll a través de TODOS los documentos
        print("\n🔍 Analizando cada punto...")
        
        # Usar scroll para obtener todos los puntos en batches
        page_offset = 0
        batch_size = 50
        
        all_points = []
        while True:
            results = qdrant.client.scroll(
                collection_name="docs",
                limit=batch_size,
                offset=page_offset,
                with_payload=True,
                with_vectors=False
            )
            
            if not results[0]:
                break
            
            all_points.extend(results[0])
            page_offset = results[1] if len(results) > 1 else None
            
            if not page_offset:
                break
        
        print(f"✅ Obtenidos {len(all_points)} puntos\n")
        
        # Analizar resultados
        empty_count = 0
        filled_count = 0
        by_document = defaultdict(lambda: {'empty': 0, 'filled': 0})
        empty_points = []
        
        for point in all_points:
            payload = point.payload
            page_content = payload.get('pageContent', '')
            doc_id = payload.get('metadata', {}).get('document_id', 'Unknown')
            
            if len(page_content) == 0:
                empty_count += 1
                by_document[doc_id]['empty'] += 1
                empty_points.append({
                    'id': point.id,
                    'document_id': doc_id,
                    'filename': payload.get('metadata', {}).get('filename', 'N/A'),
                    'section': payload.get('metadata', {}).get('section_title', 'N/A'),
                    'chunk_index': payload.get('metadata', {}).get('chunk_index', 'N/A')
                })
            else:
                filled_count += 1
                by_document[doc_id]['filled'] += 1
        
        # Mostrar resumen por documento
        print("📋 RESUMEN POR DOCUMENTO:")
        print("-" * 80)
        print(f"{'Doc ID':<10} {'Con Contenido':<20} {'Sin Contenido':<20} {'Total':<10}")
        print("-" * 80)
        
        for doc_id in sorted(by_document.keys(), key=str):
            stats = by_document[doc_id]
            total = stats['filled'] + stats['empty']
            print(f"{str(doc_id):<10} {stats['filled']:<20} {stats['empty']:<20} {total:<10}")
        
        print("-" * 80)
        print(f"{'TOTAL':<10} {filled_count:<20} {empty_count:<20} {len(all_points):<10}")
        print("-" * 80)
        
        # Conclusión
        print(f"\n📊 CONCLUSIÓN:")
        print(f"   • Puntos CON pageContent: {filled_count}")
        print(f"   • Puntos SIN pageContent: {empty_count}")
        print(f"   • Porcentaje completo: {(filled_count/len(all_points)*100):.1f}%")
        
        if empty_count > 0:
            print(f"\n❌ PROBLEMA DETECTADO: {empty_count} puntos tienen pageContent vacío\n")
            print("🔍 PUNTOS CON pageContent VACÍO:")
            print("-" * 80)
            
            for point in empty_points[:10]:  # Mostrar primeros 10
                print(f"\n   • ID: {point['id']}")
                print(f"     Documento ID: {point['document_id']}")
                print(f"     Archivo: {point['filename']}")
                print(f"     Sección: {point['section']}")
                print(f"     Chunk Index: {point['chunk_index']}")
            
            if len(empty_points) > 10:
                print(f"\n   ... y {len(empty_points) - 10} puntos más sin contenido")
            
            print(f"\n💡 RECOMENDACIÓN:")
            print(f"   Ejecuta: python reindex_documents.py")
        else:
            print(f"\n✅ EXCELENTE: Todos los documentos tienen pageContent completo")
        
        print("\n" + "="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 VERIFICACIÓN DETALLADA DE QDRANT\n")
    detailed_check()
