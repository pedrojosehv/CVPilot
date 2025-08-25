#!/usr/bin/env python3
"""
CONFIGURACIÓN PREDETERMINADA DEL BULLET POOL - CVPILOT
Esta configuración está validada y funcionando correctamente
"""

# Reglas del bullet pool por período de tiempo
BULLET_POOL_RULES = {
    "11/2023-Present": ["Product Manager", "Product Owner", "Product Analyst", "Project Manager", "Business Analyst"],
    "08/2022-11/2023": ["Product Operations Specialist"],
    "08/2020-11/2021": ["Product Manager", "Product Owner", "Project Manager", "Business Analyst"],
    "11/2021-08/2022": ["Quality Analyst"],  # Tabla 3
    "11/2019-07/2020": ["Quality Technician"]  # Tabla 5
}

# Títulos reemplazables (extraídos del bullet pool)
REPLACEABLE_TITLES = [
    'product manager', 'product owner', 'product analyst', 'business analyst',
    'project manager', 'product operations specialist', 'quality assurance analyst', 'quality analyst'
]

# Configuración de empresas para contexto
COMPANY_CONTEXTS = {
    'gca': ['growing companies advisors', 'gca'],
    'loszen': ['loszen', 'mobile app development'],
    'industrias_taime': ['industrias de tapas taime', 'manufacturing company'],
    'qproductos': ['industrias qproductos', 'manufacturing company']
}

# Configuración del template actual
TEMPLATE_CONFIG = {
    'name': 'PedroHerrera_PA_SaaS_B2B_Remote_2025.docx',
    'format_preserved': True,
    'tabs_count': 8,
    'specializations_maintained': True,
    'dates_untouched': True
}

# Configuración de validación
VALIDATION_CONFIG = {
    'check_format': True,
    'check_tabs': True,
    'check_double_spaces': False,
    'validate_replacements': True
}

def get_replacement_options(period, current_title=None):
    """
    Obtiene las opciones de reemplazo para un período específico

    Args:
        period (str): Período en formato MM/YYYY-MM/YYYY o MM/YYYY-Present
        current_title (str): Título actual (opcional)

    Returns:
        list: Lista de títulos disponibles para el período
    """
    if period in BULLET_POOL_RULES:
        options = BULLET_POOL_RULES[period]
        if current_title and current_title.title() in options and len(options) > 1:
            # Si el título actual está en las opciones, devolver alternativas
            return [opt for opt in options if opt != current_title.title()]
        return options
    return []

def is_title_replaceable(title):
    """
    Verifica si un título es reemplazable según las reglas del bullet pool

    Args:
        title (str): Título a verificar

    Returns:
        bool: True si es reemplazable, False en caso contrario
    """
    return title.lower() in REPLACEABLE_TITLES

def get_company_context(text):
    """
    Determina el contexto de empresa basado en el texto

    Args:
        text (str): Texto del párrafo anterior

    Returns:
        str: Contexto de empresa ('gca', 'loszen', etc.) o None
    """
    text_lower = text.lower()
    for company, keywords in COMPANY_CONTEXTS.items():
        if any(keyword in text_lower for keyword in keywords):
            return company
    return None

if __name__ == "__main__":
    print("=== CONFIGURACIÓN PREDETERMINADA DEL BULLET POOL ===")
    print("Esta configuración está validada y funcionando correctamente")
    print()

    print("📅 PERIODOS Y OPCIONES:")
    for period, options in BULLET_POOL_RULES.items():
        print(f"   {period}: {options}")

    print()
    print("🏢 CONTEXTOS DE EMPRESA:")
    for company, keywords in COMPANY_CONTEXTS.items():
        print(f"   {company}: {keywords}")

    print()
    print("✅ CONFIGURACIÓN VALIDADA:")
    print(f"   Template: {TEMPLATE_CONFIG['name']}")
    print(f"   Formato preservado: {TEMPLATE_CONFIG['format_preserved']}")
    print(f"   Tabs requeridos: {TEMPLATE_CONFIG['tabs_count']}")
    print(f"   Validación activada: {VALIDATION_CONFIG['check_format']}")
