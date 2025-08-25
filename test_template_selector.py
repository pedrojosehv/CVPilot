#!/usr/bin/env python3
"""
Template Selector Test Script
Test the intelligent template selection system
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.template_selector import TemplateSelector

def test_template_selector():
    """Test the template selector with different job scenarios"""

    print("🧪 Testing Template Selector System")
    print("=" * 50)

    # Initialize selector
    selector = TemplateSelector()

    # Test job scenarios
    test_jobs = [
        {
            'job_title_original': 'Product Analyst - Data Analytics',
            'skills': ['Python', 'SQL', 'Tableau', 'Excel'],
            'software': ['Google Analytics', 'Power BI'],
            'company': 'TechCorp'
        },
        {
            'job_title_original': 'Data Analyst - Business Intelligence',
            'skills': ['SQL', 'Python', 'R', 'Tableau'],
            'software': ['Google Analytics 4', 'Power BI'],
            'company': 'DataTech'
        },
        {
            'job_title_original': 'Product Manager - Growth',
            'skills': ['Product Strategy', 'Analytics', 'A/B Testing'],
            'software': ['Google Analytics', 'Mixpanel', 'Tableau'],
            'company': 'GrowthCo'
        }
    ]

    profile_types = ['product_management', 'data_analytics', 'product_management']

    for i, (job_data, profile_type) in enumerate(zip(test_jobs, profile_types)):
        print(f"\n📋 Test Job {i+1}: {job_data['job_title_original']}")
        print(f"   Profile: {profile_type}")
        print(f"   Skills: {', '.join(job_data['skills'][:3])}")
        print("-" * 40)

        # Find best template
        best_template = selector.find_best_template(job_data, profile_type)

        if best_template:
            print("✅ Best Template Found:")
            print(f"   File: {best_template.file_path.name}")
            print(f"   Folder: {best_template.folder_name}")
            print(f"   Score: {best_template.score:.2f}")
            print("   Match Reasons:")
            for reason in best_template.match_reasons:
                print(f"     • {reason}")
        else:
            print("❌ No suitable template found")

        print()

def test_full_integration():
    """Test the full integration with main.py"""

    print("\n🔄 Testing Full Integration")
    print("=" * 50)

    # Test command that would trigger auto-template selection
    test_command = "python -m src.main --job-id 166 --auto-template --verbose --cover-letter-only"

    print("Command to test:")
    print(f"   {test_command}")
    print("\nThis will:")
    print("   1. Load job data for ID 166")
    print("   2. Auto-select the best template from existing CVs")
    print("   3. Generate only a cover letter")
    print("   4. Use the selected template for content generation")
    print("\nTo run this test:")
    print(f"   cd {Path.cwd()}")
    print(f"   {test_command}")

if __name__ == "__main__":
    test_template_selector()
    test_full_integration()
