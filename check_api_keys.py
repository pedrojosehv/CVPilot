#!/usr/bin/env python3
"""
Script para verificar estado de API keys
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.api_key_manager import get_api_stats, get_api_key

def check_api_keys():
    """Verificar estado de las API keys"""
    
    print("🔑 VERIFICANDO ESTADO DE API KEYS")
    print("=" * 50)
    
    # Obtener estadísticas
    stats = get_api_stats()
    
    print(f"📊 Estadísticas:")
    print(f"   - Total de keys: {stats['total_keys']}")
    print(f"   - Keys saludables: {stats['healthy_keys']}")
    print(f"   - Estrategia actual: {stats['rotation_strategy']}")
    print(f"   - Índice actual: {stats['current_index']}")
    
    print(f"\n📈 Uso por key:")
    for key, usage in stats['key_usage'].items():
        print(f"   - ...{key[-4:]}: {usage} usos")
    
    print(f"\n❌ Errores por key:")
    if stats['key_errors']:
        for key, errors in stats['key_errors'].items():
            print(f"   - ...{key[-4:]}: {errors} errores")
    else:
        print("   - Sin errores registrados")
    
    # Probar obtener una key
    print(f"\n🧪 Probando obtención de key:")
    test_key = get_api_key("least_errors")
    if test_key:
        print(f"   ✅ Key obtenida: ...{test_key[-4:]}")
    else:
        print(f"   ❌ No se pudo obtener key")
    
    # Probar con estrategia round_robin
    print(f"\n🧪 Probando round_robin:")
    for i in range(3):
        test_key = get_api_key("round_robin")
        if test_key:
            print(f"   {i+1}. Key obtenida: ...{test_key[-4:]}")
        else:
            print(f"   {i+1}. ❌ No se pudo obtener key")

if __name__ == "__main__":
    check_api_keys()
