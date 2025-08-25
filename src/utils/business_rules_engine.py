"""
Business Rules Engine - Central validation and compliance system
Ensures all CVPilot operations follow bullet pool rules and business logic
"""

from typing import Dict, List, Any, Optional, Tuple
from ..utils.logger import LoggerMixin

class BusinessRulesEngine(LoggerMixin):
    """Central engine for business rules validation and enforcement"""

    def __init__(self):
        super().__init__()

        # BULLET POOL RULES - STRICT DEFINITIONS
        self.bullet_pool_titles = [
            'product manager',           # Table 6, 9
            'product owner',             # Table 6, 9
            'product analyst',           # Table 6
            'business analyst',          # Table 6, 9
            'project manager',           # Table 6, 9
            'product operations specialist',  # Table 7
            'quality assurance analyst',  # Table 8
            'quality analyst'            # Table 3
        ]

        # VALID CONTEXTS FOR REPLACEMENT
        self.valid_contexts = ['gca', 'loszen', 'growing companies']

        # RULES DEFINITIONS
        self.rules = {
            'title_replacement': {
                'description': 'Replace titles only if: 1) Not in bullet pool, AND 2) In valid context',
                'conditions': ['not_in_bullet_pool', 'in_valid_context'],
                'action': 'replace_title'
            },
            'cv_title_validation': {
                'description': 'CV main title should match job requirements',
                'conditions': ['title_alignment'],
                'action': 'validate_or_replace'
            },
            'content_alignment': {
                'description': 'Generated content should align with job requirements',
                'conditions': ['role_match', 'skills_match'],
                'action': 'validate_content'
            }
        }

    def validate_title_replacement(self, current_title: str, target_title: str,
                                 context_company: str = None) -> Dict[str, Any]:
        """
        Validate if a title replacement is allowed according to business rules

        Args:
            current_title: Title currently in the CV
            target_title: Job title we want to use
            context_company: Company context (GCA, Loszen, etc.)

        Returns:
            Dict with validation result and explanation
        """
        current_clean = current_title.lower().strip()
        target_clean = target_title.lower().strip()

        # RULE 1: Is current title already in bullet pool?
        current_in_pool = current_clean in self.bullet_pool_titles

        # RULE 2: Is context valid for replacement?
        context_valid = False
        if context_company:
            context_valid = any(valid_ctx in context_company.lower()
                              for valid_ctx in self.valid_contexts)

        # RULE 3: CRITICAL - Should we replace?
        # If current title is ALREADY in bullet pool, NEVER replace
        if current_in_pool:
            should_replace = False
        else:
            # Only replace if not in bullet pool AND valid context
            should_replace = context_valid

        # RULE 4: Is replacement meaningful?
        is_meaningful = current_clean != target_clean

        result = {
            'should_replace': should_replace and is_meaningful,
            'current_in_bullet_pool': current_in_pool,
            'context_valid': context_valid,
            'is_meaningful_change': is_meaningful,
            'explanation': self._explain_decision(current_in_pool, context_valid, is_meaningful),
            'rule_applied': 'title_replacement'
        }

        self.log_info(f"🎯 BUSINESS RULE VALIDATION: {result['explanation']}")
        return result

    def validate_cv_title_replacement(self, current_title: str, target_title: str) -> Dict[str, Any]:
        """
        Validate CV main title replacement - MUST follow bullet pool rules
        """
        current_clean = current_title.lower().strip()
        target_clean = target_title.lower().strip()

        # CRITICAL: Check if current title is already in bullet pool
        current_in_pool = current_clean in self.bullet_pool_titles
        target_in_pool = target_clean in self.bullet_pool_titles

        # If current title is in pool AND target is also in pool, check if replacement makes sense
        if current_in_pool and target_in_pool:
            # Allow replacement between different bullet pool titles if they are different
            if current_clean != target_clean:
                result = {
                    'should_replace': True,
                    'similarity_score': 0.5,  # Medium similarity for different pool titles
                    'current_title': current_title,
                    'target_title': target_title,
                    'current_in_bullet_pool': True,
                    'target_in_bullet_pool': True,
                    'explanation': f"CV title replacement between bullet pool titles: {current_clean} → {target_clean}"
                }
                self.log_info(f"🎯 CV TITLE VALIDATION: {result['explanation']}")
                return result
            else:
                # Same title, no replacement needed
                result = {
                    'should_replace': False,
                    'similarity_score': 1.0,
                    'current_title': current_title,
                    'target_title': target_title,
                    'current_in_bullet_pool': True,
                    'target_in_bullet_pool': True,
                    'explanation': f"CV title already matches target - NO REPLACEMENT NEEDED"
                }
                self.log_info(f"🎯 CV TITLE VALIDATION: {result['explanation']}")
                return result

        # If current title is in pool but target is not, don't replace (preserve bullet pool titles)
        if current_in_pool and not target_in_pool:
            result = {
                'should_replace': False,
                'similarity_score': 1.0,
                'current_title': current_title,
                'target_title': target_title,
                'current_in_bullet_pool': True,
                'target_in_bullet_pool': False,
                'explanation': f"CV title is in bullet pool, preserving it - NO REPLACEMENT"
            }
            self.log_info(f"🎯 CV TITLE VALIDATION: {result['explanation']}")
            return result

        # If current title is not in pool, check similarity with target
        title_matches = self._calculate_title_similarity(current_clean, target_clean)
        should_replace = title_matches < 0.7  # Replace if less than 70% similar

        result = {
            'should_replace': should_replace,
            'similarity_score': title_matches,
            'current_title': current_title,
            'target_title': target_title,
            'current_in_bullet_pool': False,
            'target_in_bullet_pool': target_in_pool,
            'explanation': f"CV title similarity: {title_matches:.1%} - {'Replace' if should_replace else 'Keep'}"
        }

        self.log_info(f"🎯 CV TITLE VALIDATION: {result['explanation']}")
        return result

    def audit_replacements(self, replacements_log: List[Dict]) -> Dict[str, Any]:
        """
        Audit a batch of replacements for rule compliance

        Args:
            replacements_log: List of replacement operations performed

        Returns:
            Audit report with compliance status
        """
        violations = []
        compliant = []

        for replacement in replacements_log:
            if replacement.get('type') == 'title_replacement':
                validation = self.validate_title_replacement(
                    replacement.get('current_title', ''),
                    replacement.get('new_title', ''),
                    replacement.get('context', '')
                )

                if replacement.get('was_replaced', False) != validation['should_replace']:
                    violations.append({
                        'replacement': replacement,
                        'expected': validation['should_replace'],
                        'explanation': validation['explanation']
                    })
                else:
                    compliant.append(replacement)

        audit_report = {
            'total_replacements': len(replacements_log),
            'compliant_count': len(compliant),
            'violation_count': len(violations),
            'compliance_rate': len(compliant) / len(replacements_log) if replacements_log else 0,
            'violations': violations,
            'status': 'COMPLIANT' if len(violations) == 0 else 'VIOLATIONS_FOUND'
        }

        if violations:
            self.log_warning(f"🚨 BUSINESS RULE VIOLATIONS FOUND: {len(violations)}")
            for violation in violations:
                self.log_warning(f"   - {violation['explanation']}")
        else:
            self.log_info("✅ ALL REPLACEMENTS COMPLIANT WITH BUSINESS RULES")

        return audit_report

    def _explain_decision(self, current_in_pool: bool, context_valid: bool,
                         is_meaningful: bool) -> str:
        """Generate human-readable explanation for replacement decision"""
        if current_in_pool:
            return "Current title already in bullet pool - NO REPLACEMENT ALLOWED (bullet pool rule)"
        elif not context_valid:
            return "Not in valid context (GCA/Loszen) - NO REPLACEMENT ALLOWED"
        elif not is_meaningful:
            return "Change not meaningful - NO REPLACEMENT NEEDED"
        else:
            return "Valid replacement: not in bullet pool + valid context + meaningful change"

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        words1 = set(title1.lower().split())
        words2 = set(title2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def get_rule_definitions(self) -> Dict[str, Any]:
        """Get all business rule definitions for documentation"""
        return {
            'bullet_pool_titles': self.bullet_pool_titles,
            'valid_contexts': self.valid_contexts,
            'rules': self.rules,
            'version': '1.0',
            'last_updated': '2025-08-25'
        }
