#!/usr/bin/env python3
"""
Script para debuggear la detección de fechas
"""

from docx import Document
from pathlib import Path

def debug_date_detection():
    print('🔍 DEBUGGEANDO DETECCIÓN DE FECHAS')
    print('=' * 60)
    
    # Buscar el CV más reciente
    output_dir = Path('output')
    docx_files = []
    for file_path in output_dir.rglob('*.docx'):
        if not file_path.name.startswith('~$'):
            docx_files.append(file_path)
    
    if not docx_files:
        print('❌ No se encontraron archivos .docx')
        return
    
    latest_file = max(docx_files, key=lambda x: x.stat().st_mtime)
    print(f'📄 Archivo: {latest_file}')
    
    try:
        doc = Document(str(latest_file))
        
        in_experience_section = False
        
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            if 'PROFESSIONAL EXPERIENCE' in text.upper():
                in_experience_section = True
                continue
            
            if in_experience_section:
                # Buscar títulos de experiencia
                if not text.startswith('•') and not text.startswith('-') and not text.startswith('*'):
                    if any(keyword in text.lower() for keyword in ['manager', 'analyst', 'specialist']):
                        if len(text) < 100:
                            print(f'\n🎯 TÍTULO: "{text}"')
                            print(f'   Longitud: {len(text)}')
                            print(f'   Contiene tab: {"\\t" in repr(text)}')
                            print(f'   Contiene espacios múltiples: {"   " in text}')
                            print(f'   Contiene dash: {" - " in text}')
                            print(f'   Contiene en-dash: {" – " in text}')
                            
                            # Analizar estructura
                            if '\t' in text:
                                parts = text.split('\t')
                                print(f'   Partes por tab: {len(parts)}')
                                for j, part in enumerate(parts):
                                    print(f'     Parte {j}: "{part}"')
                            
                            if '   ' in text:
                                parts = text.split('   ')
                                print(f'   Partes por espacios: {len(parts)}')
                                for j, part in enumerate(parts):
                                    print(f'     Parte {j}: "{part}"')
                            
                            if ' - ' in text:
                                parts = text.split(' - ')
                                print(f'   Partes por dash: {len(parts)}')
                                for j, part in enumerate(parts):
                                    print(f'     Parte {j}: "{part}"')
                            
                            if ' – ' in text:
                                parts = text.split(' – ')
                                print(f'   Partes por en-dash: {len(parts)}')
                                for j, part in enumerate(parts):
                                    print(f'     Parte {j}: "{part}"')
                            
                            # Verificar si contiene fechas
                            date_indicators = ['Present', '2023', '2022', '2021', '2020', '2019']
                            has_date = any(indicator in text for indicator in date_indicators)
                            print(f'   Contiene fecha: {has_date}')
                            
                            if has_date:
                                for indicator in date_indicators:
                                    if indicator in text:
                                        print(f'     Indicador encontrado: {indicator}')
        
        print('\n🔍 ANÁLISIS COMPLETO')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    debug_date_detection()

