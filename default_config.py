#!/usr/bin/env python3
"""
CONFIGURACIÓN PREDETERMINADA DEL SISTEMA CVPILOT
Importar este archivo para usar la configuración validada
"""

import sys
import os

# Importar la configuración del backup validado
sys.path.append("config_backup_20250824_173955")
from default_bullet_pool_config import *

# Configuración de rutas
CONFIG = {
    'template_path': 'templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx',
    'backup_dir': 'config_backup_20250824_173955',
    'output_dir': 'output',
    'logs_dir': 'logs'
}

# Configuración del sistema
SYSTEM_CONFIG = {
    'validation_enabled': True,
    'format_preservation': True,
    'context_detection': True,
    'debug_mode': False,
    'auto_backup': True
}

def validate_system():
    """Función rápida para validar que el sistema esté configurado correctamente"""
    import subprocess

    try:
        # Ejecutar el script de validación
        result = subprocess.run([
            sys.executable,
            "config_backup_20250824_173955/validate_system.py"
        ], capture_output=True, text=True)

        print("=== VALIDACIÓN DEL SISTEMA ===")
        print(result.stdout)

        if result.returncode == 0:
            print("✅ Sistema validado correctamente")
            return True
        else:
            print("❌ Problemas detectados en la validación")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error ejecutando validación: {e}")
        return False

def get_template_path():
    """Retorna la ruta del template validado"""
    return CONFIG['template_path']

def get_bullet_pool_rules():
    """Retorna las reglas del bullet pool"""
    return BULLET_POOL_RULES

def get_replaceable_titles():
    """Retorna los títulos reemplazables"""
    return REPLACEABLE_TITLES

if __name__ == "__main__":
    print("=== CONFIGURACIÓN PREDETERMINADA CVPILOT ===")
    print("Ejecutando validación del sistema...")

    if validate_system():
        print("\n🎯 Sistema listo para usar")
        print(f"📄 Template: {get_template_path()}")
        print(f"📋 Reglas del bullet pool: {len(get_bullet_pool_rules())} períodos")
        print(f"🏷️  Títulos reemplazables: {len(get_replaceable_titles())}")
    else:
        print("\n⚠️  Revisar configuración del sistema")
