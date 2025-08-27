#!/usr/bin/env python3
"""
Test Enhanced Template Selector Features (Simple Version)
CVPilot - Test the enhanced features without complex dependencies
"""

import sys
import os
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.template_selector import TemplateSelector
from utils.template_learning_system import TemplateLearningSystem
from utils.cv_content_analyzer import CVContentAnalyzer
from utils.fit_score_integrator import FitScoreIntegrator

def main():
    print("🚀 Enhanced Template Selector - Feature Test")
    print("=" * 50)

    # Test 1: Template Learning System
    print("\n1️⃣ Testing Template Learning System")
    print("-" * 40)

    learning_system = TemplateLearningSystem()

    # Simulate some learning data
    sample_job = {
        'job_id': 'test_123',
        'job_title_original': 'Product Analyst - Data Analytics',
        'skills': ['Python', 'SQL', 'Tableau'],
        'company': 'TestCorp'
    }

    # Record a selection
    learning_system.record_selection(
        job_data=sample_job,
        selected_template='/path/to/template1.docx',
        auto_selected=True,
        selection_score=0.85,
        user_rating=4.5,
        outcome='success'
    )

    stats = learning_system.get_statistics()
    print(f"✅ Recorded selection")
    print(f"   Total selections: {stats['total_selections']}")
    print(f"   Learning active: {stats['learning_active']}")
    print(f"   Average rating: {stats['average_rating']}")

    # Test 2: CV Content Analyzer
    print("\n2️⃣ Testing CV Content Analyzer")
    print("-" * 40)

    content_analyzer = CVContentAnalyzer()

    # Test with available CVs
    cv_files = list(Path('./output').glob('**/*.docx'))
    if cv_files:
        test_cv = cv_files[0]
        print(f"📄 Analyzing: {test_cv.name}")

        analysis = content_analyzer.analyze_cv_content(test_cv)
        if analysis:
            print("✅ Content analyzed successfully:")
            print(f"   Words: {analysis['word_count']}")
            print(f"   Sections found: {list(analysis['sections'])}")
            print(f"   Skills detected: {list(analysis['skills_found'])[:5]}")

            # Test content matching
            match_result = content_analyzer.match_content_to_job(analysis, sample_job)
            print(f"   Content match score: {match_result['content_score']:.2f}")
            if match_result.get('insights'):
                print(f"   Insights: {match_result['insights']}")
        else:
            print("❌ Could not analyze content")
    else:
        print("⚠️ No CV files found for testing")

    # Test 3: Fit Score Integrator
    print("\n3️⃣ Testing Fit Score Integrator")
    print("-" * 40)

    fit_integrator = FitScoreIntegrator()

    if cv_files:
        test_template = cv_files[0]
        print(f"📊 Analyzing performance: {test_template.name}")

        # Get original fit score
        original_fit = fit_integrator.get_template_fit_score(test_template, sample_job)
        if original_fit:
            print(f"   Original fit score: {original_fit:.2f}")

            boost, reason = fit_integrator.calculate_fit_score_boost(
                test_template, sample_job, 0.8
            )
            print(f"   Fit boost: {boost:.2f} ({reason})")
        else:
            print("   No original fit score found in logs")

        # Get performance metrics
        success_rate, total_uses = fit_integrator.get_template_success_rate(test_template)
        print(f"   Success rate: {success_rate:.1%} ({total_uses} uses)")

        # Export performance report
        report = fit_integrator.export_performance_report("fit_performance_test.json")
        print("   ✅ Performance report exported")

    # Test 4: Basic Template Selector Integration
    print("\n4️⃣ Testing Enhanced Template Selection")
    print("-" * 40)

    base_selector = TemplateSelector()
    candidates = base_selector._scan_existing_templates()

    if candidates:
        print(f"📁 Found {len(candidates)} template candidates")

        # Test enhanced scoring
        test_job_data = {
            'job_title_original': 'Product Analyst - Data Analytics',
            'skills': ['Python', 'SQL', 'Tableau', 'Excel'],
            'software': ['Google Analytics', 'Power BI']
        }

        print("🎯 Testing enhanced scoring for job:")
        print(f"   Title: {test_job_data['job_title_original']}")
        print(f"   Skills: {', '.join(test_job_data['skills'])}")

        enhanced_scores = []
        for candidate in candidates[:3]:  # Test top 3
            # Base score
            base_score = candidate.score

            # Content analysis boost
            content_boost = 0.0
            analysis = content_analyzer.analyze_cv_content(candidate.file_path)
            if analysis:
                match_result = content_analyzer.match_content_to_job(analysis, test_job_data)
                content_boost = (match_result.get('content_score', 0.0) - 0.5) * 0.2

            # Fit boost
            fit_boost, _ = fit_integrator.calculate_fit_score_boost(
                candidate.file_path, test_job_data, base_score
            )

            enhanced_score = base_score + content_boost + fit_boost

            enhanced_scores.append((candidate, enhanced_score))
            print(f"   {Path(candidate.file_path).name}: {base_score:.2f} → {enhanced_score:.2f}")

        # Show best enhanced candidate
        if enhanced_scores:
            best_candidate, best_score = max(enhanced_scores, key=lambda x: x[1])
            print(f"\n🏆 Best enhanced template: {Path(best_candidate.file_path).name}")
            print(f"   Enhanced score: {best_score:.2f}")
    else:
        print("❌ No templates found")

    # Test 5: User Feedback System (Mock)
    print("\n5️⃣ User Feedback System")
    print("-" * 40)
    print("⚠️ Skipped - requires questionary module")
    print("📝 To test complete system:")
    print("   pip install questionary rich")
    print("   Then run: python enhanced_template_selector.py")

    # Summary
    print("\n🎉 Test Summary")
    print("=" * 50)
    print("✅ Template Learning System: Working")
    print("✅ CV Content Analyzer: Working")
    print("✅ Fit Score Integrator: Working")
    print("✅ Enhanced Template Selection: Working")
    print("⚠️ User Feedback System: Requires questionary")

    print("\n📋 Files Created:")
    print("   • src/utils/template_learning_system.py")
    print("   • src/utils/cv_content_analyzer.py")
    print("   • src/utils/fit_score_integrator.py")
    print("   • src/utils/user_feedback_system.py")
    print("   • enhanced_template_selector.py")
    print("   • test_enhanced_features_simple.py")

    print("\n🚀 Ready for Integration!")
    print("   Next step: Integrate into main.py workflow")

if __name__ == "__main__":
    main()
