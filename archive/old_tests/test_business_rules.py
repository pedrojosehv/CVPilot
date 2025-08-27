#!/usr/bin/env python3
"""
Test script for Business Rules Engine
Validates that CVPilot follows bullet pool rules correctly
"""

import sys
import os
sys.path.append('src')

from src.utils.business_rules_engine import BusinessRulesEngine
from src.template.docx_processor import DocxProcessor

def test_business_rules():
    """Test the business rules engine"""
    print("🧪 TESTING BUSINESS RULES ENGINE")
    print("=" * 50)

    # Initialize engines
    rules_engine = BusinessRulesEngine()
    doc_processor = DocxProcessor()

    # Test 1: Title already in bullet pool should NOT be replaced
    print("\n📋 TEST 1: Title in bullet pool")
    validation1 = rules_engine.validate_title_replacement(
        current_title="Product Analyst",
        target_title="Quality Analyst",
        context_company="GCA"
    )
    print(f"   Current: 'Product Analyst' → Target: 'Quality Analyst'")
    print(f"   Should replace: {validation1['should_replace']}")
    print(f"   Explanation: {validation1['explanation']}")
    assert not validation1['should_replace'], "Should NOT replace if current title is in bullet pool"

    # Test 2: Title in bullet pool should NOT be replaced (even in valid context)
    print("\n📋 TEST 2: Title in bullet pool should NOT be replaced")
    validation2 = rules_engine.validate_title_replacement(
        current_title="Quality Assurance Analyst",
        target_title="Product Analyst",
        context_company="Loszen"
    )
    print(f"   Current: 'Quality Assurance Analyst' → Target: 'Product Analyst'")
    print(f"   Should replace: {validation2['should_replace']}")
    print(f"   Explanation: {validation2['explanation']}")
    assert not validation2['should_replace'], "Should NOT replace if current title is in bullet pool"

    # Test 3: Title not in bullet pool should be replaced (in valid context)
    print("\n📋 TEST 3: Title not in bullet pool, valid context")
    validation3 = rules_engine.validate_title_replacement(
        current_title="Digital Trainer",  # Not in bullet pool
        target_title="Product Analyst",
        context_company="GCA"  # Valid context
    )
    print(f"   Current: 'Digital Trainer' → Target: 'Product Analyst'")
    print(f"   Should replace: {validation3['should_replace']}")
    print(f"   Explanation: {validation3['explanation']}")
    assert validation3['should_replace'], "Should replace if current title not in bullet pool and valid context"

    # Test 4: Title not in bullet pool, invalid context should NOT be replaced
    print("\n📋 TEST 4: Title not in bullet pool, invalid context")
    validation4 = rules_engine.validate_title_replacement(
        current_title="Digital Trainer",  # Not in bullet pool
        target_title="Product Analyst",
        context_company="Microsoft"  # Invalid context
    )
    print(f"   Current: 'Digital Trainer' → Target: 'Product Analyst'")
    print(f"   Should replace: {validation4['should_replace']}")
    print(f"   Explanation: {validation4['explanation']}")
    assert not validation4['should_replace'], "Should NOT replace if not in valid context"

    # Test 5: CV title validation
    print("\n📋 TEST 5: CV title validation")
    cv_validation1 = rules_engine.validate_cv_title_replacement(
        current_title="PRODUCT ANALYST",
        target_title="Product Analyst - Integrations Team"
    )
    print(f"   Current: 'PRODUCT ANALYST' → Target: 'Product Analyst - Integrations Team'")
    print(f"   Similarity: {cv_validation1['similarity_score']:.1%}")
    print(f"   Should replace: {cv_validation1['should_replace']}")

    cv_validation2 = rules_engine.validate_cv_title_replacement(
        current_title="DIGITAL ANALYST",
        target_title="Product Analyst - Integrations Team"
    )
    print(f"   Current: 'DIGITAL ANALYST' → Target: 'Product Analyst - Integrations Team'")
    print(f"   Similarity: {cv_validation2['similarity_score']:.1%}")
    print(f"   Should replace: {cv_validation2['should_replace']}")

    # Test 6: Audit functionality
    print("\n📋 TEST 6: Audit functionality")
    mock_replacements = [
        {
            'type': 'title_replacement',
            'current_title': 'Product Analyst',
            'new_title': 'Quality Analyst',
            'context': 'GCA',
            'was_replaced': False  # Correct: already in bullet pool
        },
        {
            'type': 'title_replacement',
            'current_title': 'Digital Trainer',
            'new_title': 'Product Analyst',
            'context': 'GCA',
            'was_replaced': True  # Correct: not in bullet pool, valid context
        },
        {
            'type': 'title_replacement',
            'current_title': 'Digital Trainer',
            'new_title': 'Product Analyst',
            'context': 'Microsoft',
            'was_replaced': False  # Correct: not in bullet pool, invalid context
        }
    ]

    audit_report = rules_engine.audit_replacements(mock_replacements)
    print(f"   Audit status: {audit_report['status']}")
    print(f"   Compliance rate: {audit_report['compliance_rate']:.1%}")
    print(f"   Violations found: {audit_report['violation_count']}")

    print("\n✅ ALL TESTS PASSED!")
    print("🎯 Business Rules Engine is working correctly")
    print("📋 Bullet pool rules are being enforced properly")

    return True

def test_integration():
    """Test integration with DocxProcessor"""
    print("\n🔗 TESTING INTEGRATION WITH DOCX PROCESSOR")
    print("=" * 50)

    # Test that DocxProcessor has access to BusinessRulesEngine
    doc_processor = DocxProcessor()

    # Check that business rules engine is available
    assert hasattr(doc_processor, 'business_rules'), "DocxProcessor should have business_rules attribute"
    assert hasattr(doc_processor.business_rules, 'validate_title_replacement'), "Should have validation method"

    print("✅ Integration test passed!")
    print("📋 DocxProcessor has access to BusinessRulesEngine")

    return True

if __name__ == "__main__":
    try:
        test_business_rules()
        test_integration()
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("🚀 Business Rules Engine is ready for production use")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
