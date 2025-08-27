#!/usr/bin/env python3
"""
Script para verificar el contenido del CV más reciente generado
"""

from docx import Document
from pathlib import Path
import glob
import os

def verify_latest_cv():
    print('🔍 VERIFICANDO CV MÁS RECIENTE')
    print('=' * 60)
    
    # Buscar el CV más reciente
    output_dir = Path('output')
    if not output_dir.exists():
        print('❌ No se encontró la carpeta output')
        return
    
    # Buscar todos los archivos .docx en output
    docx_files = list(output_dir.rglob('*.docx'))
    if not docx_files:
        print('❌ No se encontraron archivos .docx en output')
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
        print('🎯 ANÁLISIS DE TÍTULOS DE EXPERIENCIA:')
        print('=' * 60)
        
        if experience_titles:
            print(f'✅ Se encontraron {len(experience_titles)} títulos de experiencia:')
            for i, title in enumerate(experience_titles, 1):
                print(f'   {i}. {title}')
                
                # Verificar capitalización
                if title[0].islower():
                    print(f'      ❌ ERROR: Título en minúsculas')
                else:
                    print(f'      ✅ Capitalización correcta')
                
                # Verificar si contiene "Project Manager"
                if 'project manager' in title.lower():
                    print(f'      ✅ Contiene "Project Manager"')
                else:
                    print(f'      ❌ NO contiene "Project Manager"')
        else:
            print('❌ No se encontraron títulos de experiencia')
        
        print()
        print('🔍 VERIFICACIÓN COMPLETA')
        
    except Exception as e:
        print(f'❌ Error al leer el archivo: {e}')

if __name__ == '__main__':
    verify_latest_cv()

