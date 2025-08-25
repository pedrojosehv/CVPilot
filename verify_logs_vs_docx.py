#!/usr/bin/env python3
"""
Script para verificar que los logs coincidan con el contenido real del DOCX
"""

from docx import Document
from pathlib import Path
import re

def verify_logs_vs_docx():
    print('🔍 VERIFICACIÓN COMPLETA: LOGS vs DOCX')
    print('=' * 80)
    
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
    print(f'📄 Archivo analizado: {latest_file}')
    print(f'🕐 Última modificación: {latest_file.stat().st_mtime}')
    print()
    
    try:
        doc = Document(str(latest_file))
        
        print('📋 CONTENIDO REAL DEL DOCX:')
        print('=' * 80)
        
        in_experience_section = False
        experience_titles = []
        all_content = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            all_content.append(f'Línea {i+1}: {text}')
            
            if 'PROFESSIONAL EXPERIENCE' in text.upper():
                in_experience_section = True
                print(f'📝 Línea {i+1}: {text}')
                continue
            
            if in_experience_section:
                # Buscar títulos de experiencia
                if not text.startswith('•') and not text.startswith('-') and not text.startswith('*'):
                    if any(keyword in text.lower() for keyword in ['manager', 'analyst', 'specialist']):
                        if len(text) < 100:
                            experience_titles.append({
                                'line': i+1,
                                'text': text,
                                'index': i
                            })
                            print(f'🎯 TÍTULO: Línea {i+1}: "{text}"')
                else:
                    # Es un bullet point
                    print(f'   • {text}')
            else:
                print(f'📝 Línea {i+1}: {text}')
        
        print()
        print('🔍 ANÁLISIS DETALLADO DE TÍTULOS:')
        print('=' * 80)
        
        if experience_titles:
            print(f'✅ Se encontraron {len(experience_titles)} títulos de experiencia:')
            
            for j, title_info in enumerate(experience_titles, 1):
                print(f'\n{j}. Línea {title_info["line"]}: "{title_info["text"]}"')
                
                # Analizar estructura
                if '\t' in title_info["text"]:
                    parts = title_info["text"].split('\t')
                    print(f'   📋 Partes por tab: {len(parts)}')
                    for k, part in enumerate(parts):
                        print(f'      Parte {k}: "{part}"')
                
                # Verificar si tiene fecha
                if any(date_indicator in title_info["text"] for date_indicator in ['Present', '2023', '2022', '2021', '2020', '2019']):
                    print(f'   📅 Contiene fecha')
                else:
                    print(f'   ❌ Sin fecha')
                
                # Verificar si tiene especialidad
                if '(' in title_info["text"] and ')' in title_info["text"]:
                    specialization = title_info["text"][title_info["text"].find('('):title_info["text"].find(')')+1]
                    print(f'   📋 Especialidad: {specialization}')
                else:
                    print(f'   ❌ Sin especialidad')
                
                # Verificar si es de GCA
                if 'GCA' in title_info["text"] or 'Growing Companies' in title_info["text"] or 'Project Manager' in title_info["text"]:
                    print(f'   🏢 ES TÍTULO DE GCA')
                else:
                    print(f'   🏢 NO es título de GCA')
        
        print()
        print('🔍 COMPARACIÓN CON LOGS ESPERADOS:')
        print('=' * 80)
        
        # Según los logs, deberíamos ver:
        expected_replacements = [
            "Product Manager (SaaS platforms) → Project Manager (SaaS platforms)",
            "Digital Product Specialist (SaaS platforms) → Project Manager (SaaS platforms)",
            "Business Analyst (essentials) → Project Manager (essentials)"
        ]
        
        expected_skipped = [
            "Quality and Business Analyst (NO reemplazar)",
            "Digital Product Specialist (NO reemplazar)",
            "Quality Analyst (NO reemplazar)"
        ]
        
        print('✅ REEMPLAZOS ESPERADOS (según logs):')
        for replacement in expected_replacements:
            print(f'   - {replacement}')
        
        print('\n🚫 TÍTULOS QUE NO DEBERÍAN CAMBIAR (según logs):')
        for skipped in expected_skipped:
            print(f'   - {skipped}')
        
        print()
        print('🔍 VERIFICACIÓN DE COINCIDENCIA:')
        print('=' * 80)
        
        # Verificar si los reemplazos esperados están en el DOCX
        found_replacements = []
        found_skipped = []
        
        for title_info in experience_titles:
            title_text = title_info["text"]
            
            # Verificar reemplazos
            if "Project Manager (SaaS platforms)" in title_text:
                found_replacements.append(f"✅ Project Manager (SaaS platforms) encontrado en línea {title_info['line']}")
            
            if "Project Manager (essentials)" in title_text:
                found_replacements.append(f"✅ Project Manager (essentials) encontrado en línea {title_info['line']}")
            
            # Verificar títulos que no deberían cambiar
            if "Quality and Business Analyst" in title_text:
                found_skipped.append(f"✅ Quality and Business Analyst mantenido en línea {title_info['line']}")
            
            if "Digital Product Specialist" in title_text and "Project Manager" not in title_text:
                found_skipped.append(f"✅ Digital Product Specialist mantenido en línea {title_info['line']}")
            
            if "Quality Analyst" in title_text:
                found_skipped.append(f"✅ Quality Analyst mantenido en línea {title_info['line']}")
        
        print('✅ REEMPLAZOS ENCONTRADOS EN DOCX:')
        for found in found_replacements:
            print(f'   - {found}')
        
        print('\n🚫 TÍTULOS MANTENIDOS EN DOCX:')
        for found in found_skipped:
            print(f'   - {found}')
        
        print()
        print('🔍 PROBLEMAS DETECTADOS:')
        print('=' * 80)
        
        # Buscar inconsistencias
        problems = []
        
        # Verificar si hay títulos que deberían haberse reemplazado pero no
        for title_info in experience_titles:
            title_text = title_info["text"]
            
            # Si hay "Digital Product Specialist" sin "Project Manager", es un problema
            if "Digital Product Specialist" in title_text and "Project Manager" not in title_text:
                problems.append(f"❌ PROBLEMA: 'Digital Product Specialist' no fue reemplazado en línea {title_info['line']}")
            
            # Si hay "Product Manager" sin "Project Manager", es un problema
            if "Product Manager" in title_text and "Project Manager" not in title_text:
                problems.append(f"❌ PROBLEMA: 'Product Manager' no fue reemplazado en línea {title_info['line']}")
        
        if problems:
            print('❌ PROBLEMAS ENCONTRADOS:')
            for problem in problems:
                print(f'   {problem}')
        else:
            print('✅ No se encontraron problemas - los logs coinciden con el DOCX')
        
        print()
        print('📊 RESUMEN FINAL:')
        print('=' * 80)
        
        total_titles = len(experience_titles)
        total_replacements = len([r for r in found_replacements if "Project Manager" in r])
        total_skipped = len(found_skipped)
        
        print(f'📈 Total de títulos encontrados: {total_titles}')
        print(f'✅ Reemplazos realizados: {total_replacements}')
        print(f'🚫 Títulos mantenidos: {total_skipped}')
        print(f'❌ Problemas detectados: {len(problems)}')
        
        if len(problems) == 0:
            print('\n🎉 ¡VERIFICACIÓN EXITOSA! Los logs coinciden con el DOCX.')
        else:
            print('\n⚠️ VERIFICACIÓN FALLIDA: Los logs NO coinciden con el DOCX.')
        
    except Exception as e:
        print(f'❌ Error al leer el archivo: {e}')

if __name__ == '__main__':
    verify_logs_vs_docx()

