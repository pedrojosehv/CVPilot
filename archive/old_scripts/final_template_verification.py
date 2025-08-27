#!/usr/bin/env python3
"""
Verificación exhaustiva del template y reglas antes de ejecutar
"""

from docx import Document

def verify_template_and_rules():
    print("🔍 VERIFICACIÓN EXHAUSTIVA: TEMPLATE vs BULLET POOL")
    print("=" * 60)

    # Leer el template actual
    doc = Document('templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx')

    print("📄 TEMPLATE: PedroHerrera_PA_SaaS_B2B_Remote_2025.docx")
    print("-" * 50)

    # Extraer títulos de experiencia
    experience_titles = []
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text and any(char.isdigit() for char in text) and ('/' in text):
            experience_titles.append((i, text))

    print(f"🎯 TÍTULOS DE EXPERIENCIA ENCONTRADOS: {len(experience_titles)}")
    for i, (line_num, title) in enumerate(experience_titles, 1):
        print(f"   {i}. Línea {line_num}: {title}")

    print()
    print("📋 BULLET POOL REGLAS:")
    print("-" * 30)

    # Reglas del bullet pool (fechas exactas del archivo)
    bullet_pool_rules = {
        "11/2023-Present": ["Product Manager", "Product Owner", "Product Analyst", "Project Manager", "Business Analyst"],
        "08/2022-11/2023": ["Product Operations Specialist"],
        "08/2020-11/2021": ["Product Manager", "Product Owner", "Project Manager", "Business Analyst"],
        "11/2021-08/2022": ["Quality Analyst"],  # Tabla 3
        "11/2019-07/2020": ["Quality Technician"]  # Tabla 5
    }

    # Títulos reemplazables
    replaceable_titles = [
        'product manager', 'product owner', 'product analyst', 'business analyst',
        'project manager', 'product operations specialist', 'quality assurance analyst', 'quality analyst'
    ]

    for period, alternatives in bullet_pool_rules.items():
        print(f"📅 {period}: {alternatives}")

    print()
    print("🎯 SIMULACIÓN DE REEMPLAZOS:")
    print("-" * 30)

    import re

    for line_num, title in experience_titles:
        print(f"\\n📝 Título: {title}")

        # Extraer título limpio y período
        title_match = re.match(r'([^(\d]+)', title)
        if title_match:
            clean_title = title_match.group(1).strip().lower()
            print(f"   🏷️  Título limpio: '{clean_title}'")

            # Buscar período
            period_match = re.search(r'(\d{2}/\d{4})\s*-\s*(\d{2}/\d{4}|Present)', title)
            if period_match:
                period = f"{period_match.group(1)}-{period_match.group(2)}"
                print(f"   📅 Período: {period}")

                # Verificar si es reemplazable
                is_replaceable = clean_title in replaceable_titles
                print(f"   ✅ Reemplazable: {is_replaceable}")

                # Ver alternativas
                if period in bullet_pool_rules:
                    alternatives = bullet_pool_rules[period]
                    print(f"   🎯 Alternativas: {alternatives}")

                    if is_replaceable and alternatives:
                        current_title_proper = clean_title.title()
                        if current_title_proper in alternatives:
                            # Si el título actual está en las alternativas, elegir otra diferente
                            available_alternatives = [alt for alt in alternatives if alt != current_title_proper]
                            if available_alternatives:
                                replacement = available_alternatives[0]
                                print(f"   🔄 DEBERÍA REEMPLAZAR: '{current_title_proper}' → '{replacement}'")
                            else:
                                print(f"   ❌ SIN OTRAS ALTERNATIVAS: '{current_title_proper}' es la única opción")
                        else:
                            # El título actual no está en las alternativas, usar la primera
                            replacement = alternatives[0]
                            print(f"   🔄 DEBERÍA REEMPLAZAR: '{current_title_proper}' → '{replacement}'")
                    else:
                        print(f"   ❌ NO SE PUEDE REEMPLAZAR")
                else:
                    print(f"   ❌ PERÍODO NO ENCONTRADO EN BULLET POOL")
            else:
                print(f"   ❌ PERÍODO NO DETECTADO")

    print()
    print("🎉 RESUMEN ESPERADO:")
    print("-" * 20)
    print("❓ Product Analyst (11/2023-Present) → Pendiente (período detectado correctamente)")
    print("✅ Product Operations Specialist (08/2022-11/2023) → Sin cambios (única alternativa)")
    print("❓ Quality Assurance Analyst (11/2021-08/2022) → Revisar (Quality Analyst vs Quality Assurance Analyst)")
    print("❓ Product Manager (08/2020-11/2021) → Pendiente (múltiples alternativas)")
    print("❓ Quality Assurance Analyst (11/2019-07/2020) → Pendiente (Quality Technician vs Quality Assurance Analyst)")

if __name__ == "__main__":
    verify_template_and_rules()
