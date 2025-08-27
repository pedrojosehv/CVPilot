#!/usr/bin/env python3
"""
Script para debuggear el problema de duplicación de títulos
"""

from docx import Document
from pathlib import Path

def debug_duplication_issue():
    print('🔍 DEBUGGEANDO PROBLEMA DE DUPLICACIÓN')
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
        gca_titles = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            if 'PROFESSIONAL EXPERIENCE' in text.upper():
                in_experience_section = True
                print(f'📝 Línea {i+1}: {text}')
                continue
            
            if in_experience_section:
                # Buscar títulos de experiencia
                if not text.startswith('•') and not text.startswith('-') and not text.startswith('*'):
                    if any(keyword in text.lower() for keyword in ['manager', 'analyst', 'specialist']):
                        if len(text) < 100:
                            print(f'\n🎯 TÍTULO ENCONTRADO: "{text}"')
                            print(f'   Línea: {i+1}')
                            print(f'   Longitud: {len(text)}')
                            
                            # Verificar si es de GCA
                            if 'GCA' in text or 'Growing Companies' in text or 'Project Manager' in text:
                                gca_titles.append({
                                    'line': i+1,
                                    'text': text,
                                    'index': i
                                })
                                print(f'   ✅ ES TÍTULO DE GCA')
                            else:
                                print(f'   ❌ NO es título de GCA')
        
        print('\n🔍 ANÁLISIS DE TÍTULOS GCA:')
        print('=' * 60)
        
        if gca_titles:
            print(f'✅ Se encontraron {len(gca_titles)} títulos de GCA:')
            
            for j, title_info in enumerate(gca_titles, 1):
                print(f'   {j}. Línea {title_info["line"]}: "{title_info["text"]}"')
                
                # Verificar si es duplicado
                if j > 1:
                    prev_title = gca_titles[j-2]["text"]
                    if title_info["text"] == prev_title:
                        print(f'      ❌ DUPLICADO: Mismo texto que el anterior')
                    else:
                        print(f'      ✅ DIFERENTE: Texto único')
                
                # Analizar estructura
                if '\t' in title_info["text"]:
                    parts = title_info["text"].split('\t')
                    print(f'      📋 Partes por tab: {len(parts)}')
                    for k, part in enumerate(parts):
                        print(f'        Parte {k}: "{part}"')
                
                # Verificar si tiene fecha
                if any(date_indicator in title_info["text"] for date_indicator in ['Present', '2023', '2022', '2021', '2020', '2019']):
                    print(f'      📅 Contiene fecha')
                else:
                    print(f'      ❌ Sin fecha')
                
                # Verificar si tiene especialidad
                if '(' in title_info["text"] and ')' in title_info["text"]:
                    specialization = title_info["text"][title_info["text"].find('('):title_info["text"].find(')')+1]
                    print(f'      📋 Especialidad: {specialization}')
                else:
                    print(f'      ❌ Sin especialidad')
        else:
            print('❌ No se encontraron títulos de GCA')
        
        print('\n🔍 VERIFICACIÓN DE DUPLICACIÓN:')
        print('=' * 60)
        
        # Verificar si hay títulos idénticos
        unique_titles = set()
        duplicates = []
        
        for title_info in gca_titles:
            if title_info["text"] in unique_titles:
                duplicates.append(title_info["text"])
            else:
                unique_titles.add(title_info["text"])
        
        if duplicates:
            print(f'❌ PROBLEMA: Se encontraron {len(duplicates)} títulos duplicados:')
            for duplicate in duplicates:
                print(f'   - "{duplicate}"')
        else:
            print(f'✅ No se encontraron títulos duplicados')
        
        print('\n🔍 ANÁLISIS COMPLETO')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    debug_duplication_issue()

