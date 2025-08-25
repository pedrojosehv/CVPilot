#!/usr/bin/env python3
"""
Simple test script for CVPilot
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test basic imports"""
    print("🔧 Testing basic imports...")
    
    try:
        from utils.config import Config
        print("✓ Config imported successfully")
        
        from utils.logger import setup_logger
        print("✓ Logger imported successfully")
        
        from utils.models import JobData, ProfileConfig
        print("✓ Models imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from utils.config import Config
        config = Config()
        print("✓ Configuration created successfully")
        print(f"  Data path: {config.data_path}")
        print(f"  Templates path: {config.templates_path}")
        print(f"  Default template: {config.default_template_path}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_logger():
    """Test logger"""
    print("\n📝 Testing logger...")
    
    try:
        from utils.logger import setup_logger
        logger = setup_logger()
        logger.info("Test log message")
        print("✓ Logger working")
        return True
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False

def test_template_exists():
    """Test if template exists"""
    print("\n📄 Testing template...")
    
    template_path = Path("templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx")
    if template_path.exists():
        print(f"✓ Template found: {template_path}")
        print(f"  Size: {template_path.stat().st_size} bytes")
        return True
    else:
        print(f"❌ Template not found: {template_path}")
        return False

def test_profiles():
    """Test profiles"""
    print("\n👤 Testing profiles...")
    
    profile_path = Path("profiles/product_management.json")
    if profile_path.exists():
        print(f"✓ Profile found: {profile_path}")
        return True
    else:
        print(f"❌ Profile not found: {profile_path}")
        return False

def test_data_files():
    """Test data files"""
    print("\n📊 Testing data files...")
    
    datapm_path = Path("../../DataPM/csv/src/csv_processed")
    if datapm_path.exists():
        csv_files = list(datapm_path.glob("*.csv"))
        if csv_files:
            print(f"✓ Found {len(csv_files)} CSV files")
            for csv_file in csv_files:
                print(f"  - {csv_file.name}")
            return True
        else:
            print("⚠️  No CSV files found in DataPM directory")
            return False
    else:
        print(f"⚠️  DataPM path not found: {datapm_path}")
        return False

def main():
    """Main test function"""
    print("🧪 CVPilot Simple Test")
    print("=" * 50)
    
    tests = [
        test_basic_imports,
        test_config,
        test_logger,
        test_template_exists,
        test_profiles,
        test_data_files
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! CVPilot is ready to use.")
        print("\nNext steps:")
        print("1. Copy env.example to .env and add your API keys")
        print("2. Run: python -m src.main --job-id 0 --profile-type product_management --dry-run")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
