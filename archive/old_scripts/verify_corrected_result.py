#!/usr/bin/env python3
"""
Script para verificar el resultado corregido del CV
"""

from docx import Document
from pathlib import Path
import glob
import os

def verify_corrected_cv():
    print('🔍 VERIFICANDO RESULTADO CORREGIDO DEL CV')
    print('=' * 60)
    
    # Buscar el CV más reciente (excluyendo archivos temporales)
    output_dir = Path('output')
    if not output_dir.exists():
        print('❌ No se encontró la carpeta output')
        return
    
    # Buscar todos los archivos .docx en output (excluyendo temporales)
    docx_files = []
    for file_path in output_dir.rglob('*.docx'):
        if not file_path.name.startswith('~$'):  # Excluir archivos temporales
            docx_files.append(file_path)
    
    if not docx_files:
        print('❌ No se encontraron archivos .docx válidos en output')
        return
    
    # Obtener el archivo más reciente
    latest_file = max(docx_files, key=lambda x: x.stat().st_mtime)
    
    print(f'📄 Archivo más reciente: {latest_file}')
    print(f'🕐 Última modificación: {latest_file.stat().st_mtime}')
    print()
    
    # Leer el contenido
    try:
        doc = Document(str(latest_file))
        
        print('📋 CONTENIDO DEL CV:')
        print('=' * 60)
        
        in_experience_section = False
        experience_titles = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            # Detectar sección de experiencia
            if 'PROFESSIONAL EXPERIENCE' in text.upper():
                in_experience_section = True
                print(f'📝 Línea {i+1}: {text}')
                continue
            
            if in_experience_section:
                # Buscar títulos de experiencia (sin bullet points)
                if not text.startswith('•') and not text.startswith('-') and not text.startswith('*'):
                    # Verificar si es un título de trabajo
                    if any(keyword in text.lower() for keyword in ['manager', 'analyst', 'specialist', 'coordinator']):
                        if len(text) < 100:  # Títulos suelen ser cortos
                            experience_titles.append(text)
                            print(f'🎯 TÍTULO ENCONTRADO: {text}')
                        else:
                            print(f'📝 Línea {i+1}: {text}')
                    else:
                        print(f'📝 Línea {i+1}: {text}')
                else:
                    # Es un bullet point
                    print(f'   • {text}')
            else:
                print(f'📝 Línea {i+1}: {text}')
        
        print()
        print('🎯 ANÁLISIS DE CORRECCIONES:')
        print('=' * 60)
        
        if experience_titles:
            print(f'✅ Se encontraron {len(experience_titles)} títulos de experiencia:')
            
            # Verificar las correcciones específicas
            corrections_made = {
                'dates_preserved': 0,
                'specializations_preserved': 0,
                'digital_product_specialist_replaced': False,
                'correct_replacements': 0
            }
            
            for i, title in enumerate(experience_titles, 1):
                print(f'   {i}. {title}')
                
                # Verificar capitalización
                if title[0].islower():
                    print(f'      ❌ ERROR: Título en minúsculas')
                else:
                    print(f'      ✅ Capitalización correcta')
                
                # Verificar preservación de fechas
                if any(date_indicator in title for date_indicator in ['Present', '2023', '2022', '2021', '2020', '2019']):
                    print(f'      ✅ Fecha preservada')
                    corrections_made['dates_preserved'] += 1
                else:
                    print(f'      ❌ ERROR: Fecha faltante')
                
                # Verificar preservación de especialidades
                if '(' in title and ')' in title:
                    specialization = title[title.find('('):title.find(')')+1]
                    print(f'      ✅ Especialidad preservada: {specialization}')
                    corrections_made['specializations_preserved'] += 1
                
                # Verificar reemplazo de Digital Product Specialist
                if 'Digital Product Specialist' in title:
                    print(f'      ❌ ERROR: Digital Product Specialist NO fue reemplazado')
                elif 'Project Manager' in title and any(date in title for date in ['08/2022', '11/2023']):
                    print(f'      ✅ CORRECTO: Digital Product Specialist fue reemplazado por Project Manager')
                    corrections_made['digital_product_specialist_replaced'] = True
                    corrections_made['correct_replacements'] += 1
                
                # Verificar otros reemplazos correctos
                elif 'Project Manager' in title:
                    print(f'      ✅ CORRECTO: Reemplazo realizado')
                    corrections_made['correct_replacements'] += 1
                else:
                    print(f'      ✅ CORRECTO: Título mantenido (sin alternativas)')
        
        print()
        print('📊 RESUMEN DE CORRECCIONES:')
        print('=' * 60)
        print(f'✅ Fechas preservadas: {corrections_made["dates_preserved"]}')
        print(f'✅ Especialidades preservadas: {corrections_made["specializations_preserved"]}')
        print(f'✅ Digital Product Specialist reemplazado: {"SÍ" if corrections_made["digital_product_specialist_replaced"] else "NO"}')
        print(f'✅ Reemplazos correctos totales: {corrections_made["correct_replacements"]}')
        
        # Verificar que se cumplieron los objetivos
        print()
        print('🎯 VERIFICACIÓN DE OBJETIVOS:')
        print('=' * 60)
        
        if corrections_made['dates_preserved'] > 0:
            print('✅ OBJETIVO 1: Fechas preservadas - CUMPLIDO')
        else:
            print('❌ OBJETIVO 1: Fechas preservadas - FALLIDO')
        
        if corrections_made['specializations_preserved'] > 0:
            print('✅ OBJETIVO 2: Tipografía de especialidades preservada - CUMPLIDO')
        else:
            print('❌ OBJETIVO 2: Tipografía de especialidades preservada - FALLIDO')
        
        if corrections_made['digital_product_specialist_replaced']:
            print('✅ OBJETIVO 3: Digital Product Specialist reemplazado por Project Manager - CUMPLIDO')
        else:
            print('❌ OBJETIVO 3: Digital Product Specialist reemplazado por Project Manager - FALLIDO')
        
        print()
        print('🔍 VERIFICACIÓN COMPLETA')
        
    except Exception as e:
        print(f'❌ Error al leer el archivo: {e}')

if __name__ == '__main__':
    verify_corrected_cv()

