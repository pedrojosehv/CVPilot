#!/usr/bin/env python3
"""
Script para verificar la lógica de reemplazo de títulos
"""

def verify_replacement_logic():
    print("🔍 VERIFICACIÓN DE LÓGICA DE REEMPLAZO")
    print("=" * 50)

    # Reglas del bullet pool (como están implementadas)
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

    # Títulos que se pueden reemplazar
    replaceable_titles = [
        'product manager',
        'product owner',
        'product analyst',
        'business analyst',
        'digital product specialist',
        'product specialist',
        'quality assurance analyst',
        'quality analyst'
    ]

    print("📋 CONDICIONES ACTUALES:")
    print("-" * 30)
    print(f"✅ Títulos reemplazables: {replaceable_titles}")
    print()

    for period, companies in period_roles.items():
        print(f"📅 Período: {period}")
        for company, options in companies.items():
            print(f"   🏢 {company}: {options if options else '❌ Sin alternativas'}")
        print()

    print("🎯 LÓGICA ESPERADA:")
    print("-" * 30)
    print("✅ Digital Product Specialist en 08/2022-11/2023 (GCA) → Product Operations Specialist")
    print("✅ Digital Product Specialist en 11/2023-Present (GCA) → Project Manager (primera opción)")
    print("✅ Digital Product Specialist en 08/2020-11/2021 (Loszen) → Project Manager (primera opción)")
    print("❌ Digital Product Specialist en 08/2022-11/2023 (Loszen) → Sin cambios")
    print()

if __name__ == "__main__":
    verify_replacement_logic()
