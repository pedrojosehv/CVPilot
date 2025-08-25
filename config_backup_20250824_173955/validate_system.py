#!/usr/bin/env python3
"""
SCRIPT DE VALIDACIÓN DEL SISTEMA CVPILOT
Verifica que la configuración esté funcionando correctamente
"""

import os
import sys
from pathlib import Path
from docx import Document
import re

def validate_template_exists():
    """Valida que el template esté en la ubicación correcta"""
    template_path = "templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx"
    if os.path.exists(template_path):
        print("✅ Template encontrado:", template_path)
        return True
    else:
        print("❌ Template NO encontrado:", template_path)
        return False

def validate_template_format():
    """Valida el formato del template"""
    template_path = "templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx"
    try:
        doc = Document(template_path)
        noddok_found = False
        loszen_found = False

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if 'Noddok Saas Application' in text:
                noddok_found = True
                tabs_count = text.count('\t')
                has_double_space = '  ' in text
                print(f"✅ Noddok encontrado - Tabs: {tabs_count}, Doble espacio: {has_double_space}")
                if tabs_count == 8 and not has_double_space:
                    print("   ✅ Formato correcto")
                else:
                    print("   ❌ Formato incorrecto")

            elif '08/2020' in text and '11/2021' in text:
                loszen_found = True
                tabs_count = text.count('\t')
                has_double_space = '  ' in text
                print(f"✅ Loszen encontrado - Tabs: {tabs_count}, Doble espacio: {has_double_space}")
                if tabs_count == 8 and not has_double_space:
                    print("   ✅ Formato correcto")
                else:
                    print("   ❌ Formato incorrecto")

        if noddok_found and loszen_found:
            print("✅ Template format validated successfully")
            return True
        else:
            print("❌ Missing expected content in template")
            return False

    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

def validate_config_file():
    """Valida que el archivo de configuración existe y es correcto"""
    config_path = "config_backup_20250824_173955/default_bullet_pool_config.py"
    if os.path.exists(config_path):
        print("✅ Config file found:", config_path)
        try:
            # Importar y validar la configuración
            sys.path.append("config_backup_20250824_173955")
            import default_bullet_pool_config as config

            # Verificar que las reglas principales existan
            if hasattr(config, 'BULLET_POOL_RULES'):
                print(f"✅ BULLET_POOL_RULES found with {len(config.BULLET_POOL_RULES)} periods")
            else:
                print("❌ BULLET_POOL_RULES not found")
                return False

            if hasattr(config, 'REPLACEABLE_TITLES'):
                print(f"✅ REPLACEABLE_TITLES found with {len(config.REPLACEABLE_TITLES)} titles")
            else:
                print("❌ REPLACEABLE_TITLES not found")
                return False

            print("✅ Config file validated successfully")
            return True

        except Exception as e:
            print(f"❌ Error validating config: {e}")
            return False
    else:
        print("❌ Config file not found:", config_path)
        return False

def validate_backup_files():
    """Valida que los archivos de backup existan"""
    backup_dir = "config_backup_20250824_173955"
    required_files = [
        "default_bullet_pool_config.py",
        "README_CONFIG.md",
        "validate_system.py"
    ]

    all_found = True
    for file in required_files:
        file_path = os.path.join(backup_dir, file)
        if os.path.exists(file_path):
            print(f"✅ Backup file found: {file}")
        else:
            print(f"❌ Backup file missing: {file}")
            all_found = False

    return all_found

def run_full_validation():
    """Ejecuta la validación completa del sistema"""
    print("=== VALIDACIÓN COMPLETA DEL SISTEMA CVPILOT ===")
    print("Fecha:", os.popen("date").read().strip())
    print()

    tests = [
        ("Template exists", validate_template_exists),
        ("Template format", validate_template_format),
        ("Config file", validate_config_file),
        ("Backup files", validate_backup_files),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        print()

    print("=== RESULTADOS DE VALIDACIÓN ===")
    print(f"✅ Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 SISTEMA 100% VALIDADO - LISTO PARA USAR")
        return True
    else:
        print("⚠️  Algunos tests fallaron - Revisar configuración")
        return False

if __name__ == "__main__":
    success = run_full_validation()
    sys.exit(0 if success else 1)
