#!/usr/bin/env python3
"""
CVPilot Test Setup Script
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import Config
from utils.logger import setup_logger
from ingest.job_loader import JobLoader

def test_config():
    """Test configuration loading"""
    print("🔧 Testing configuration...")
    
    try:
        config = Config()
        print("✓ Configuration loaded successfully")
        print(f"  Data path: {config.data_path}")
        print(f"  Templates path: {config.templates_path}")
        print(f"  Profiles path: {config.profiles_path}")
        print(f"  LLM provider: {config.llm_config.provider}")
        print(f"  LLM model: {config.llm_config.model}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_logger():
    """Test logger setup"""
    print("\n📝 Testing logger...")
    
    try:
        logger = setup_logger()
        logger.info("Test log message")
        print("✓ Logger setup successful")
        return True
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False

def test_job_loader():
    """Test job loader"""
    print("\n📊 Testing job loader...")
    
    try:
        config = Config()
        loader = JobLoader(config.data_path)
        
        # Get statistics
        stats = loader.get_job_statistics()
        
        if stats:
            print("✓ Job loader working")
            print(f"  Total jobs: {stats.get('total_jobs', 0)}")
            print(f"  Unique companies: {stats.get('unique_companies', 0)}")
            print(f"  Unique skills: {stats.get('unique_skills', 0)}")
        else:
            print("⚠️  No jobs loaded (check DataPM path)")
        
        return True
    except Exception as e:
        print(f"❌ Job loader error: {e}")
        return False

def test_profiles():
    """Test profile loading"""
    print("\n👤 Testing profiles...")
    
    try:
        config = Config()
        profile_files = config.get_profile_files()
        
        if profile_files:
            print(f"✓ Found {len(profile_files)} profile file(s)")
            for profile_file in profile_files:
                print(f"  - {profile_file.name}")
        else:
            print("⚠️  No profile files found")
        
        return True
    except Exception as e:
        print(f"❌ Profile test error: {e}")
        return False

def test_templates():
    """Test template loading"""
    print("\n📄 Testing templates...")
    
    try:
        config = Config()
        template_files = config.get_template_files()
        
        if template_files:
            print(f"✓ Found {len(template_files)} template file(s)")
            for template_file in template_files:
                print(f"  - {template_file.name}")
        else:
            print("⚠️  No template files found")
            print("   Please add .docx template files to templates/ folder")
        
        return True
    except Exception as e:
        print(f"❌ Template test error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 CVPilot Test Setup")
    print("=" * 50)
    
    tests = [
        test_config,
        test_logger,
        test_job_loader,
        test_profiles,
        test_templates
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
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
