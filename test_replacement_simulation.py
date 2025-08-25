#!/usr/bin/env python3
"""
Simulación de reemplazos que deberían ocurrir según las reglas
"""

def simulate_replacements():
    print("🎭 SIMULACIÓN DE REEMPLAZOS ESPERADOS")
    print("=" * 50)

    # Títulos actuales en el template (según el último log)
    current_titles = [
        ("Product Manager (SaaS platforms) 11/2023 - Present", "GCA"),
        ("Digital Product Specialist (SaaS platforms) 08/2022 - 11/2023", "GCA"),
        ("Digital Product Specialist 08/2020 - 11/2021", "Loszen")
    ]

    # Reglas del bullet pool
    period_roles = {
        "11/2023-Present": {
            "GCA": ["Product Manager", "Product Owner", "Product Analyst", "Project Manager", "Business Analyst"],
            "Loszen": []
        },
        "08/2022-11/2023": {
            "GCA": ["Product Operations Specialist"],
            "Loszen": []
        },
        "08/2020-11/2021": {
            "GCA": [],
            "Loszen": ["Product Manager", "Product Owner", "Project Manager", "Business Analyst"]
        }
    }

    # Títulos reemplazables
    replaceable_titles = [
        'product manager', 'product owner', 'product analyst', 'business analyst',
        'digital product specialist', 'product specialist',
        'quality assurance analyst', 'quality analyst'
    ]

    print("📋 ANÁLISIS DE CADA TÍTULO:")
    print("-" * 40)

    for original_title, company in current_titles:
        print(f"\\n🎯 Título original: '{original_title}'")

        # Detectar período PRIMERO (antes de limpiar)
        import re

        # Extraer período usando regex simple y directa
        import re

        # Patrón específico para los formatos que vemos: MM/YYYY - MM/YYYY o MM/YYYY - Present
        date_pattern = r'(\d{2}/\d{4})\s*-\s*(\d{2}/\d{4}|Present)'

        period = "Unknown"
        match = re.search(date_pattern, original_title)
        if match:
            start_date = match.group(1)
            end_date = match.group(2)
            period = f"{start_date}-{end_date}"
        print(f"   📅 Período detectado: '{period}'")

        # Extraer el título limpio (sin fechas ni paréntesis)
        title_clean = re.sub(r'\\d{2}/\\d{4}', '', original_title)  # Remove dates
        title_clean = re.sub(r'Present', '', title_clean)
        title_clean = re.sub(r'[-–—]+', '', title_clean)
        title_clean = title_clean.split('(')[0].strip().lower()
        print(f"   📝 Título limpio: '{title_clean}'")

        # Verificar si es reemplazable
        is_replaceable = title_clean in replaceable_titles
        print(f"   ✅ Es reemplazable: {is_replaceable}")

        if is_replaceable and period in period_roles:
            alternatives = period_roles[period].get(company, [])
            print(f"   🎯 Alternativas disponibles: {alternatives}")

            if alternatives:
                replacement = alternatives[0]  # Primera opción
                print(f"   🔄 DEBERÍA REEMPLAZAR: '{original_title.split('(')[0].strip()}' → '{replacement}'")
            else:
                print(f"   ❌ NO DEBE REEMPLAZAR: Sin alternativas disponibles")
        else:
            print(f"   ❌ NO DEBE REEMPLAZAR: No cumple condiciones")

    print("\\n" + "=" * 50)
    print("🎉 RESUMEN ESPERADO:")
    print("✅ 1 reemplazo: Product Manager → Project Manager (11/2023-Present)")
    print("❌ 0 cambios: Digital Product Specialist (08/2022-11/2023) - sin alternativas")
    print("❌ 0 cambios: Digital Product Specialist (08/2020-11/2021) - Loszen no tiene alternativas en este período")

if __name__ == "__main__":
    simulate_replacements()
