#!/usr/bin/env python3
"""
Comparar los templates disponibles para ver cuál tiene más títulos de experiencia
"""

from docx import Document
import os

def analyze_template(template_path):
    """Analizar un template y contar títulos de experiencia"""
    try:
        doc = Document(template_path)

        titles_found = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            # Buscar patrones que indiquen títulos de experiencia
            if any(keyword in text.upper() for keyword in ['PROFESSIONAL EXPERIENCE', 'EXPERIENCE', 'WORK EXPERIENCE']):
                # Este es el header de experiencia, buscar los siguientes párrafos
                continue

            # Detectar títulos que contienen fechas (patrón MM/YYYY)
            import re
            if re.search(r'\d{2}/\d{4}', text):
                # Es un título con fecha
                titles_found.append(text)

        return titles_found

    except Exception as e:
        print(f"Error analizando {template_path}: {e}")
        return []

def compare_templates():
    print("🔍 COMPARANDO TEMPLATES DISPONIBLES")
    print("=" * 50)

    templates_dir = "templates"
    template_files = [
        "CV Pedro Herrera.docx",
        "PedroHerrera_PA_SaaS_B2B_Remote_2025.docx"
    ]

    for template_file in template_files:
        template_path = os.path.join(templates_dir, template_file)

        if os.path.exists(template_path):
            print(f"\n📄 {template_file}:")
            titles = analyze_template(template_path)

            print(f"   📊 Títulos encontrados: {len(titles)}")
            for i, title in enumerate(titles, 1):
                print(f"   {i}. {title}")
        else:
            print(f"\n❌ {template_file}: NO ENCONTRADO")

    print("\n" + "=" * 50)
    print("💡 RECOMENDACIÓN: Usar el template con más títulos de experiencia")

if __name__ == "__main__":
    compare_templates()
