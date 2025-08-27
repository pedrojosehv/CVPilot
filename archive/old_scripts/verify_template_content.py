#!/usr/bin/env python3
"""
Verificación detallada del contenido del template
"""

from docx import Document
import os

def verify_template_content():
    template_path = 'templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx'

    print(f'📁 Archivo: {template_path}')
    print(f'📊 Tamaño: {os.path.getsize(template_path)} bytes')
    print(f'⏰ Modificación: {os.path.getmtime(template_path)}')
    print()

    doc = Document(template_path)
    print('=== TODO EL CONTENIDO DEL TEMPLATE ===')
    print()

    all_text = []
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text:
            print(f'[{i:2d}] {repr(text)}')  # Usar repr para ver caracteres especiales
            all_text.append(text)

    print()
    print('=== BÚSQUEDA ESPECÍFICA ===')
    search_terms = ['Product Analyst', '11/2023', 'Present', 'Noddok', 'SaaS Application']

    print('🔍 TÉRMINOS BUSCADOS:')
    for term in search_terms:
        found_lines = []
        for i, text in enumerate(all_text):
            if term.lower() in text.lower():
                found_lines.append(f'línea {i}')

        if found_lines:
            print(f'✅ \"{term}\": ENCONTRADO en {", ".join(found_lines)}')
        else:
            print(f'❌ \"{term}\": NO ENCONTRADO')

    print()
    print('=== ANÁLISIS DETALLADO ===')
    print(f'📊 Total de párrafos con texto: {len(all_text)}')

    # Contar elementos que podrían ser títulos
    potential_titles = []
    for text in all_text:
        if len(text) < 100 and (',' in text or '(' in text or ')' in text):
            potential_titles.append(text)

    print(f'📋 Posibles títulos/empresas: {len(potential_titles)}')
    for title in potential_titles:
        print(f'   • {title}')

if __name__ == "__main__":
    verify_template_content()
