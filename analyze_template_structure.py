#!/usr/bin/env python3
"""
Script para analizar la estructura completa del template
"""

from docx import Document
from pathlib import Path

def analyze_template_structure():
    print('🔍 ANALIZANDO ESTRUCTURA COMPLETA DEL TEMPLATE')
    print('=' * 80)
    
    template_path = "templates/CV_PH - Innovation specialist.docx"
    print(f'📄 Template: {template_path}')
    
    try:
        doc = Document(template_path)
        
        print('\n📋 CONTENIDO COMPLETO DEL TEMPLATE:')
        print('=' * 80)
        
        in_experience_section = False
        experience_entries = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            print(f'📝 Línea {i+1}: "{text}"')
            
            if 'PROFESSIONAL EXPERIENCE' in text.upper():
                in_experience_section = True
                continue
            
            if in_experience_section:
                # Buscar nombres de empresas
                if any(company in text.lower() for company in ['gca', 'growing companies', 'loszen', 'taime', 'qproductos']):
                    print(f'🏢 EMPRESA DETECTADA en línea {i+1}: "{text}"')
                    experience_entries.append({
                        'line': i+1,
                        'type': 'company',
                        'text': text
                    })
                
                # Buscar títulos de experiencia
                elif any(keyword in text.lower() for keyword in ['manager', 'analyst', 'specialist']):
                    if len(text) < 100 and not text.startswith('•'):
                        print(f'🎯 TÍTULO DETECTADO en línea {i+1}: "{text}"')
                        experience_entries.append({
                            'line': i+1,
                            'type': 'title',
                            'text': text
                        })
        
        print('\n🔍 ANÁLISIS DE ENTRADAS DE EXPERIENCIA:')
        print('=' * 80)
        
        if experience_entries:
            print(f'✅ Se encontraron {len(experience_entries)} entradas de experiencia:')
            
            for j, entry in enumerate(experience_entries, 1):
                print(f'\n{j}. Línea {entry["line"]} ({entry["type"]}): "{entry["text"]}"')
                
                if entry["type"] == "company":
                    # Analizar empresa
                    if 'gca' in entry["text"].lower() or 'growing companies' in entry["text"].lower():
                        print(f'   🏢 ES GCA')
                    elif 'loszen' in entry["text"].lower():
                        print(f'   🏢 ES LOSZEN')
                    elif 'taime' in entry["text"].lower():
                        print(f'   🏢 ES TAIME')
                    elif 'qproductos' in entry["text"].lower():
                        print(f'   🏢 ES QPRODUCTOS')
                    else:
                        print(f'   🏢 EMPRESA DESCONOCIDA')
                
                elif entry["type"] == "title":
                    # Analizar título
                    if 'digital product specialist' in entry["text"].lower():
                        print(f'   🎯 ES DIGITAL PRODUCT SPECIALIST')
                    elif 'product manager' in entry["text"].lower():
                        print(f'   🎯 ES PRODUCT MANAGER')
                    elif 'quality' in entry["text"].lower():
                        print(f'   🎯 ES QUALITY ANALYST')
                    elif 'business analyst' in entry["text"].lower():
                        print(f'   🎯 ES BUSINESS ANALYST')
        
        print('\n🔍 PROBLEMA IDENTIFICADO:')
        print('=' * 80)
        
        # Verificar si hay nombres de empresas cerca de los títulos
        company_titles = []
        for i, entry in enumerate(experience_entries):
            if entry["type"] == "company":
                # Buscar el siguiente título
                for j in range(i+1, len(experience_entries)):
                    if experience_entries[j]["type"] == "title":
                        company_titles.append({
                            'company': entry["text"],
                            'title': experience_entries[j]["text"],
                            'company_line': entry["line"],
                            'title_line': experience_entries[j]["line"]
                        })
                        break
        
        if company_titles:
            print('✅ RELACIONES EMPRESA-TÍTULO ENCONTRADAS:')
            for relation in company_titles:
                print(f'   🏢 {relation["company"]} (línea {relation["company_line"]})')
                print(f'   🎯 {relation["title"]} (línea {relation["title_line"]})')
                print()
        else:
            print('❌ NO se encontraron relaciones empresa-título claras')
            print('💡 Esto explica por qué no se detecta el contexto de empresa')
        
    except Exception as e:
        print(f'❌ Error al leer el template: {e}')

if __name__ == '__main__':
    analyze_template_structure()

