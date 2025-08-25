#!/usr/bin/env python3
"""
Script para analizar los títulos reales en el template original
"""

from docx import Document
from pathlib import Path

def analyze_template_titles():
    print('🔍 ANALIZANDO TÍTULOS DEL TEMPLATE ORIGINAL')
    print('=' * 80)
    
    template_path = "templates/CV_PH - Innovation specialist.docx"
    print(f'📄 Template: {template_path}')
    
    try:
        doc = Document(template_path)
        
        print('\n📋 CONTENIDO DEL TEMPLATE:')
        print('=' * 80)
        
        in_experience_section = False
        experience_titles = []
        
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
                            experience_titles.append({
                                'line': i+1,
                                'text': text,
                                'index': i
                            })
                            print(f'🎯 TÍTULO ORIGINAL: Línea {i+1}: "{text}"')
                else:
                    # Es un bullet point
                    print(f'   • {text}')
            else:
                print(f'📝 Línea {i+1}: {text}')
        
        print('\n🔍 ANÁLISIS DE TÍTULOS ORIGINALES:')
        print('=' * 80)
        
        if experience_titles:
            print(f'✅ Se encontraron {len(experience_titles)} títulos originales:')
            
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
                
                # Verificar si debería ser reemplazado según bullet_pool.docx
                title_lower = title_info["text"].lower()
                if 'product manager' in title_lower or 'digital product specialist' in title_lower or 'business analyst' in title_lower:
                    print(f'   🔄 DEBERÍA SER REEMPLAZADO')
                else:
                    print(f'   ✅ NO DEBERÍA SER REEMPLAZADO')
        
        print('\n🔍 COMPARACIÓN CON LOGS:')
        print('=' * 80)
        
        # Comparar con lo que dicen los logs
        print('📊 LOGS DICEN QUE SE DETECTÓ:')
        print('   - Product Manager (SaaS platforms) 11/2023 - Present')
        print('   - Digital Product Specialist (SaaS platforms) 08/2022 - 11/2023')
        print('   - Business Analyst (essentials) 01/2025')
        
        print('\n📊 TEMPLATE ORIGINAL TIENE:')
        for title_info in experience_titles:
            print(f'   - {title_info["text"]}')
        
        print('\n🔍 PROBLEMAS IDENTIFICADOS:')
        print('=' * 80)
        
        # Buscar discrepancias
        problems = []
        
        # Verificar si los títulos del template coinciden con los logs
        template_titles = [t["text"].lower() for t in experience_titles]
        
        expected_titles = [
            'product manager (saas platforms)',
            'digital product specialist (saas platforms)',
            'business analyst (essentials)'
        ]
        
        for expected in expected_titles:
            found = False
            for template_title in template_titles:
                if expected in template_title or template_title in expected:
                    found = True
                    break
            
            if not found:
                problems.append(f"❌ No se encontró '{expected}' en el template")
        
        if problems:
            print('❌ PROBLEMAS ENCONTRADOS:')
            for problem in problems:
                print(f'   {problem}')
        else:
            print('✅ Los títulos del template coinciden con los logs')
        
    except Exception as e:
        print(f'❌ Error al leer el template: {e}')

if __name__ == '__main__':
    analyze_template_titles()

