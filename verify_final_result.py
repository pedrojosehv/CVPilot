#!/usr/bin/env python3
"""
Script para verificar el resultado final del CV generado
"""

from docx import Document
from pathlib import Path
import glob
import os

def verify_final_cv():
    print('🔍 VERIFICANDO RESULTADO FINAL DEL CV')
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
            
            # Definir qué títulos deberían haberse reemplazado según bullet_pool.docx
            should_be_replaced = [
                'Product Manager (SaaS platforms)',  # Debería ser reemplazado
                'Business Analyst (essentials)'      # Debería ser reemplazado
            ]
            
            should_remain_unchanged = [
                'Digital Product Specialist (SaaS platforms)',  # NO debería ser reemplazado
                'Quality and Business Analyst',                 # NO debería ser reemplazado
                'Digital Product Specialist',                   # NO debería ser reemplazado
                'Quality Analyst'                               # NO debería ser reemplazado
            ]
            
            for i, title in enumerate(experience_titles, 1):
                print(f'   {i}. {title}')
                
                # Verificar capitalización
                if title[0].islower():
                    print(f'      ❌ ERROR: Título en minúsculas')
                else:
                    print(f'      ✅ Capitalización correcta')
                
                # Verificar si debería haber sido reemplazado
                if any(should_replace in title for should_replace in should_be_replaced):
                    if 'Project Manager' in title:
                        print(f'      ✅ CORRECTO: Fue reemplazado con Project Manager')
                    else:
                        print(f'      ❌ ERROR: Debería haber sido reemplazado')
                
                # Verificar si debería haberse mantenido
                elif any(should_remain in title for should_remain in should_remain_unchanged):
                    if 'Project Manager' in title:
                        print(f'      ❌ ERROR: NO debería haber sido reemplazado')
                    else:
                        print(f'      ✅ CORRECTO: Se mantuvo sin cambios')
                
                # Verificar si contiene "Project Manager" cuando no debería
                elif 'Project Manager' in title:
                    print(f'      ❌ ERROR: Reemplazado incorrectamente con Project Manager')
                else:
                    print(f'      ✅ CORRECTO: Título original mantenido')
                
                # Verificar preservación de especialidades
                if '(' in title and ')' in title:
                    specialization = title[title.find('('):title.find(')')+1]
                    print(f'      📋 Especialidad: {specialization}')
        
        print()
        print('📊 RESUMEN DE VERIFICACIÓN:')
        print('=' * 60)
        
        # Contar reemplazos correctos e incorrectos
        correct_replacements = 0
        incorrect_replacements = 0
        correct_unchanged = 0
        incorrect_unchanged = 0
        
        for title in experience_titles:
            # Verificar reemplazos correctos
            if ('Product Manager (SaaS platforms)' in title and 'Project Manager (SaaS platforms)' in title) or \
               ('Business Analyst (essentials)' in title and 'Project Manager (essentials)' in title):
                correct_replacements += 1
            
            # Verificar mantenimientos correctos
            elif any(should_remain in title for should_remain in should_remain_unchanged) and 'Project Manager' not in title:
                correct_unchanged += 1
            
            # Verificar errores
            elif 'Project Manager' in title and any(should_remain in title for should_remain in should_remain_unchanged):
                incorrect_replacements += 1
            elif any(should_replace in title for should_replace in should_be_replaced) and 'Project Manager' not in title:
                incorrect_unchanged += 1
        
        print(f'✅ Reemplazos correctos: {correct_replacements}')
        print(f'✅ Títulos mantenidos correctamente: {correct_unchanged}')
        print(f'❌ Reemplazos incorrectos: {incorrect_replacements}')
        print(f'❌ Títulos no reemplazados cuando deberían: {incorrect_unchanged}')
        
        total_correct = correct_replacements + correct_unchanged
        total_incorrect = incorrect_replacements + incorrect_unchanged
        total = total_correct + total_incorrect
        
        if total > 0:
            accuracy = (total_correct / total) * 100
            print(f'📈 Precisión: {accuracy:.1f}%')
        
        print()
        print('🔍 VERIFICACIÓN COMPLETA')
        
    except Exception as e:
        print(f'❌ Error al leer el archivo: {e}')

if __name__ == '__main__':
    verify_final_cv()

