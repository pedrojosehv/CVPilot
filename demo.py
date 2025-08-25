#!/usr/bin/env python3
"""
CVPilot Demo Script
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_basic_functionality():
    """Demo basic functionality without complex imports"""
    print("🚀 CVPilot Demo")
    print("=" * 50)
    
    # Test basic imports
    try:
        from utils.config import Config
        from utils.logger import setup_logger
        print("✓ Basic imports successful")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test configuration
    try:
        config = Config()
        print(f"✓ Configuration loaded")
        print(f"  Template: {config.default_template_path}")
        print(f"  Data path: {config.data_path}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test logger
    try:
        logger = setup_logger()
        logger.info("Demo log message")
        print("✓ Logger working")
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False
    
    # Test template validation
    try:
        from template.docx_processor import DocxProcessor
        processor = DocxProcessor()
        
        if config.default_template_path.exists():
            validation = processor.validate_template(config.default_template_path)
            print(f"✓ Template validation: {validation['is_valid']}")
            print(f"  Placeholders found: {len(validation['placeholders_found'])}")
        else:
            print("⚠️  Template not found")
    except Exception as e:
        print(f"❌ Template validation error: {e}")
        return False
    
    # Test profile loading
    try:
        from matching.profile_matcher import ProfileMatcher
        matcher = ProfileMatcher(config.profiles_path)
        profiles = matcher.get_available_profiles()
        print(f"✓ Profiles loaded: {profiles}")
    except Exception as e:
        print(f"❌ Profile loading error: {e}")
        return False
    
    print("\n✅ Demo completed successfully!")
    return True

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📋 Usage Instructions:")
    print("=" * 50)
    print("1. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("2. Configure API keys:")
    print("   cp env.example .env")
    print("   # Edit .env and add your API keys")
    print()
    print("3. Run with real data:")
    print("   python -m src.main --job-id 0 --profile-type product_management --dry-run")
    print()
    print("4. Generate actual CV:")
    print("   python -m src.main --job-id 0 --profile-type product_management")
    print()
    print("5. Available options:")
    print("   --job-id: Job ID from DataPM CSV")
    print("   --profile-type: product_management (default)")
    print("   --dry-run: Generate preview only")
    print("   --verbose: Detailed output")

def main():
    """Main demo function"""
    success = demo_basic_functionality()
    
    if success:
        show_usage_instructions()
    else:
        print("\n❌ Demo failed. Please check the configuration.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
