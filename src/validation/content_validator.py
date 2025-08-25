"""
Content validation module for CVPilot
"""

import re
from typing import List, Dict, Any
from pathlib import Path

from ..utils.models import Replacements, ValidationResult, ValidationError, ReplacementBlock
from ..utils.logger import LoggerMixin

class ContentValidator(LoggerMixin):
    """Validate generated CV content"""
    
    def __init__(self):
        super().__init__()
        self.forbidden_tokens = [
            "confidential", "secret", "internal", "proprietary",
            "draft", "placeholder",
            "lorem ipsum", "sample"  # Removed "template", "example" and "demo" as they're too restrictive
        ]
        
        # Validation limits
        self.max_summary_length = 550  # Maximum 550 characters for summary (quality over strict limits)
        self.max_bullet_length = 200
        self.max_skills_count = 15
        self.max_software_count = 10
        self.min_bullets = 3
        self.max_bullets = 5
    
    def validate_replacements(self, replacements: Replacements) -> ValidationResult:
        """Validate all replacement content"""
        
        self.log_info("Starting content validation")
        
        errors = []
        warnings = []
        
        # Validate profile summary
        summary_errors, summary_warnings = self._validate_profile_summary(replacements.profile_summary)
        errors.extend(summary_errors)
        warnings.extend(summary_warnings)
        
        # Validate top bullets
        bullets_errors, bullets_warnings = self._validate_top_bullets(replacements.top_bullets)
        errors.extend(bullets_errors)
        warnings.extend(bullets_warnings)
        
        # Validate skill list
        skills_errors, skills_warnings = self._validate_skill_list(replacements.skill_list)
        errors.extend(skills_errors)
        warnings.extend(skills_warnings)
        
        # Validate software list
        software_errors, software_warnings = self._validate_software_list(replacements.software_list)
        errors.extend(software_errors)
        warnings.extend(software_warnings)
        
        # Validate objective title
        title_errors, title_warnings = self._validate_objective_title(replacements.objective_title)
        errors.extend(title_errors)
        warnings.extend(title_warnings)
        
        # Validate ATS recommendations
        ats_errors, ats_warnings = self._validate_ats_recommendations(replacements.ats_recommendations)
        errors.extend(ats_errors)
        warnings.extend(ats_warnings)
        
        # Calculate overall confidence score
        confidence_score = self._calculate_confidence_score(replacements)
        
        # Determine if validation passed
        is_valid = len(errors) == 0
        
        self.log_info(f"Validation completed: {len(errors)} errors, {len(warnings)} warnings")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            confidence_score=confidence_score
        )
    
    def _validate_profile_summary(self, summary: ReplacementBlock) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate profile summary"""
        errors = []
        warnings = []
        
        # Check length (characters, not words) and truncate if needed
        char_count = len(summary.content)
        if char_count > self.max_summary_length:
            # Truncate the content to max length
            truncated_content = summary.content[:self.max_summary_length - 3] + "..."
            summary.content = truncated_content
            self.logger.warning(f"Summary truncated from {char_count} to {self.max_summary_length} characters")

            # Add warning instead of error
            warnings.append(ValidationError(
                field="ProfileSummary",
                message=f"Summary was truncated from {char_count} to {self.max_summary_length} chars",
                severity="warning"
            ))
        elif char_count < 100:  # Minimum reasonable length in characters
            warnings.append(ValidationError(
                field="ProfileSummary",
                message=f"Summary too short: {char_count} chars (min 100 recommended)",
                severity="warning"
            ))
        
        # Check for forbidden tokens
        forbidden_found = self._check_forbidden_tokens(summary.content)
        if forbidden_found:
            errors.append(ValidationError(
                field="ProfileSummary",
                message=f"Forbidden tokens found: {', '.join(forbidden_found)}",
                severity="error"
            ))
        
        # Check for placeholder text
        if "{{" in summary.content or "}}" in summary.content:
            errors.append(ValidationError(
                field="ProfileSummary",
                message="Placeholder tags found in content",
                severity="error"
            ))
        
        # Check confidence
        if summary.confidence < 0.5:
            warnings.append(ValidationError(
                field="ProfileSummary",
                message=f"Low confidence score: {summary.confidence:.2f}",
                severity="warning"
            ))
        
        return errors, warnings
    
    def _validate_top_bullets(self, bullets: List[ReplacementBlock]) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate top bullets"""
        errors = []
        warnings = []
        
        # Check number of bullets
        if len(bullets) < self.min_bullets:
            errors.append(ValidationError(
                field="TopBullets",
                message=f"Too few bullets: {len(bullets)} (min {self.min_bullets})",
                severity="error"
            ))
        elif len(bullets) > self.max_bullets:
            warnings.append(ValidationError(
                field="TopBullets",
                message=f"Too many bullets: {len(bullets)} (max {self.max_bullets})",
                severity="warning"
            ))
        
        # Validate each bullet
        for i, bullet in enumerate(bullets):
            bullet_errors, bullet_warnings = self._validate_single_bullet(bullet, i)
            errors.extend(bullet_errors)
            warnings.extend(bullet_warnings)
        
        return errors, warnings
    
    def _validate_single_bullet(self, bullet: ReplacementBlock, index: int) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate a single bullet point"""
        errors = []
        warnings = []
        
        # Check length
        if len(bullet.content) > self.max_bullet_length:
            errors.append(ValidationError(
                field=f"TopBullets[{index}]",
                message=f"Bullet too long: {len(bullet.content)} chars (max {self.max_bullet_length})",
                severity="error"
            ))
        elif len(bullet.content) < 20:
            warnings.append(ValidationError(
                field=f"TopBullets[{index}]",
                message=f"Bullet too short: {len(bullet.content)} chars (min 20 recommended)",
                severity="warning"
            ))
        
        # Check for forbidden tokens
        forbidden_found = self._check_forbidden_tokens(bullet.content)
        if forbidden_found:
            errors.append(ValidationError(
                field=f"TopBullets[{index}]",
                message=f"Forbidden tokens found: {', '.join(forbidden_found)}",
                severity="error"
            ))
        
        # Check for action verbs
        if not self._has_action_verb(bullet.content):
            warnings.append(ValidationError(
                field=f"TopBullets[{index}]",
                message="Bullet should start with action verb",
                severity="warning"
            ))
        
        # Check for quantifiable results
        if not self._has_quantifiable_result(bullet.content):
            warnings.append(ValidationError(
                field=f"TopBullets[{index}]",
                message="Bullet should include quantifiable results",
                severity="warning"
            ))
        
        return errors, warnings
    
    def _validate_skill_list(self, skill_list: ReplacementBlock) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate skill list"""
        errors = []
        warnings = []
        
        # Handle both string and list content
        if isinstance(skill_list.content, list):
            skills = [skill.strip() for skill in skill_list.content if skill.strip()]
        else:
            skills = [skill.strip() for skill in skill_list.content.split(',') if skill.strip()]
        
        # Check number of skills
        if len(skills) > self.max_skills_count:
            warnings.append(ValidationError(
                field="SkillList",
                message=f"Too many skills: {len(skills)} (max {self.max_skills_count})",
                severity="warning"
            ))
        elif len(skills) < 5:
            warnings.append(ValidationError(
                field="SkillList",
                message=f"Too few skills: {len(skills)} (min 5 recommended)",
                severity="warning"
            ))
        
        # Check for duplicates
        duplicates = self._find_duplicates(skills)
        if duplicates:
            warnings.append(ValidationError(
                field="SkillList",
                message=f"Duplicate skills found: {', '.join(duplicates)}",
                severity="warning"
            ))
        
        # Check for forbidden tokens
        for skill in skills:
            forbidden_found = self._check_forbidden_tokens(skill)
            if forbidden_found:
                errors.append(ValidationError(
                    field="SkillList",
                    message=f"Forbidden tokens in skill '{skill}': {', '.join(forbidden_found)}",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_software_list(self, software_list: ReplacementBlock) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate software list"""
        errors = []
        warnings = []
        
        # Handle both string and list content
        if isinstance(software_list.content, list):
            software = [sw.strip() for sw in software_list.content if sw.strip()]
        else:
            software = [sw.strip() for sw in software_list.content.split(',') if sw.strip()]
        
        # Check number of software
        if len(software) > self.max_software_count:
            warnings.append(ValidationError(
                field="SoftwareList",
                message=f"Too many software: {len(software)} (max {self.max_software_count})",
                severity="warning"
            ))
        
        # Check for duplicates
        duplicates = self._find_duplicates(software)
        if duplicates:
            warnings.append(ValidationError(
                field="SoftwareList",
                message=f"Duplicate software found: {', '.join(duplicates)}",
                severity="warning"
            ))
        
        # Check for forbidden tokens
        for sw in software:
            forbidden_found = self._check_forbidden_tokens(sw)
            if forbidden_found:
                errors.append(ValidationError(
                    field="SoftwareList",
                    message=f"Forbidden tokens in software '{sw}': {', '.join(forbidden_found)}",
                    severity="error"
                ))
        
        return errors, warnings
    
    def _validate_objective_title(self, title: ReplacementBlock) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate objective title"""
        errors = []
        warnings = []
        
        # Check length
        if len(title.content) > 80:
            errors.append(ValidationError(
                field="ObjectiveTitle",
                message=f"Title too long: {len(title.content)} chars (max 80)",
                severity="error"
            ))
        elif len(title.content) < 3:
            errors.append(ValidationError(
                field="ObjectiveTitle",
                message=f"Title too short: {len(title.content)} chars (min 3)",
                severity="error"
            ))
        
        # Check for forbidden tokens
        forbidden_found = self._check_forbidden_tokens(title.content)
        if forbidden_found:
            errors.append(ValidationError(
                field="ObjectiveTitle",
                message=f"Forbidden tokens found: {', '.join(forbidden_found)}",
                severity="error"
            ))
        
        return errors, warnings
    
    def _validate_ats_recommendations(self, ats: ReplacementBlock) -> tuple[List[ValidationError], List[ValidationError]]:
        """Validate ATS recommendations"""
        errors = []
        warnings = []
        
        # Check length
        word_count = len(ats.content.split())
        if word_count > 100:
            warnings.append(ValidationError(
                field="ATSRecommendations",
                message=f"ATS recommendations too long: {word_count} words (max 100)",
                severity="warning"
            ))
        
        # Check for forbidden tokens
        forbidden_found = self._check_forbidden_tokens(ats.content)
        if forbidden_found:
            errors.append(ValidationError(
                field="ATSRecommendations",
                message=f"Forbidden tokens found: {', '.join(forbidden_found)}",
                severity="error"
            ))
        
        return errors, warnings
    
    def _check_forbidden_tokens(self, text: str) -> List[str]:
        """Check for forbidden tokens in text"""
        found = []
        text_lower = text.lower()
        
        for token in self.forbidden_tokens:
            if token.lower() in text_lower:
                found.append(token)
        
        return found
    
    def _has_action_verb(self, text: str) -> bool:
        """Check if text starts with action verb"""
        action_verbs = [
            "led", "managed", "developed", "implemented", "created", "designed",
            "improved", "increased", "reduced", "achieved", "delivered", "built",
            "launched", "optimized", "streamlined", "coordinated", "facilitated"
        ]
        
        first_word = text.split()[0].lower().rstrip('.,!?')
        return first_word in action_verbs
    
    def _has_quantifiable_result(self, text: str) -> bool:
        """Check if text contains quantifiable results"""
        # Look for numbers, percentages, currency
        patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Currency
            r'\d+%',  # Percentages
            r'\d+\.\d+',  # Decimals
            r'\d+',  # Numbers
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _find_duplicates(self, items: List[str]) -> List[str]:
        """Find duplicate items in list"""
        seen = set()
        duplicates = []
        
        for item in items:
            if item.lower() in seen:
                duplicates.append(item)
            else:
                seen.add(item.lower())
        
        return duplicates
    
    def _calculate_confidence_score(self, replacements: Replacements) -> float:
        """Calculate overall confidence score"""
        scores = [
            replacements.profile_summary.confidence,
            replacements.skill_list.confidence,
            replacements.software_list.confidence,
            replacements.objective_title.confidence,
            replacements.ats_recommendations.confidence
        ]
        
        # Add bullet confidence scores
        for bullet in replacements.top_bullets:
            scores.append(bullet.confidence)
        
        # Calculate average
        return sum(scores) / len(scores) if scores else 0.0
