"""
Template Selector - Intelligent CV Template Selection from Existing Outputs
CVPilot - Automatically selects the best CV template from previously generated outputs
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class TemplateCandidate:
    """Represents a potential CV template with scoring information"""
    file_path: Path
    folder_name: str
    role: str
    specialization: str
    tools: List[str]
    business_model: str
    year: str
    file_date: Optional[datetime]
    score: float = 0.0
    match_reasons: List[str] = None

    def __post_init__(self):
        if self.match_reasons is None:
            self.match_reasons = []

class TemplateSelector:
    """Intelligent template selector that finds the best CV match from existing outputs"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)

        # Role mappings for better matching
        self.role_mappings = {
            'product_analyst': ['PA', 'Product Analyst'],
            'data_analyst': ['DA', 'Data Analyst'],
            'product_manager': ['PM', 'Product Manager'],
            'product_owner': ['PO', 'Product Owner'],
            'project_manager': ['PJM', 'Project Manager'],
            'business_analyst': ['BA', 'Business Analyst'],
            'operations_manager': ['OM', 'Operations Manager'],
            'asistente': ['AA', 'Asistente', 'Analista']
        }

        # Specialization mappings
        self.specialization_mappings = {
            'analytics': ['ANAL', 'AIML', 'ANDE', 'ANCO'],
            'general': ['GEN'],
            'growth': ['ANTE'],
            'technical': ['CODE'],
            'agile': ['COLL'],
            'data': ['DATA']
        }

    def find_best_template(self, job_data: Dict[str, Any], profile_type: str) -> Optional[TemplateCandidate]:
        """
        Find the best template for the given job by analyzing existing CVs

        Args:
            job_data: Job description data
            profile_type: Profile type (e.g., 'product_management')

        Returns:
            Best template candidate or None if no suitable template found
        """
        candidates = self._scan_existing_templates()
        if not candidates:
            self.logger.info("No existing templates found")
            return None

        # Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score, reasons = self._score_template(candidate, job_data, profile_type)
            candidate.score = score
            candidate.match_reasons = reasons
            scored_candidates.append(candidate)

        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x.score, reverse=True)

        best_candidate = scored_candidates[0] if scored_candidates else None

        if best_candidate and best_candidate.score > 0:
            self.logger.info(f"🎯 Best template found: {best_candidate.file_path.name}")
            self.logger.info(f"   Score: {best_candidate.score:.2f}")
            self.logger.info(f"   Reasons: {', '.join(best_candidate.match_reasons)}")
            return best_candidate
        else:
            self.logger.info("No suitable template found with sufficient score")
            return None

    def _scan_existing_templates(self) -> List[TemplateCandidate]:
        """Scan output directory for existing CV templates"""
        candidates = []

        if not self.output_dir.exists():
            return candidates

        # Pattern to match CV files: PedroHerrera_{Role}_{Spec}_{Model}_{Year}.docx
        cv_pattern = re.compile(r'PedroHerrera_([A-Z]+)_([A-Z]+)_([A-Z]+)_(\d{4})\.docx$')

        for folder in self.output_dir.iterdir():
            if not folder.is_dir():
                continue

            # Skip data_analytics folder (seems to be different structure)
            if folder.name == 'data_analytics':
                continue

            for file_path in folder.glob("*.docx"):
                match = cv_pattern.match(file_path.name)
                if match:
                    role_prefix, spec_prefix, model_prefix, year = match.groups()

                    # Parse folder name to extract tools
                    tools = self._extract_tools_from_folder(folder.name)

                    # Get file modification date
                    file_date = None
                    try:
                        file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                    except:
                        pass

                    candidate = TemplateCandidate(
                        file_path=file_path,
                        folder_name=folder.name,
                        role=role_prefix,
                        specialization=spec_prefix,
                        tools=tools,
                        business_model=model_prefix,
                        year=year,
                        file_date=file_date
                    )

                    candidates.append(candidate)

        self.logger.info(f"📁 Found {len(candidates)} existing CV templates")
        return candidates

    def _extract_tools_from_folder(self, folder_name: str) -> List[str]:
        """Extract tools from folder name like 'Product Analyst - General - Python, SQL, Tableau'"""
        parts = folder_name.split(' - ')
        if len(parts) >= 3:
            tools_part = parts[2]
            # Split by comma and clean up
            tools = [tool.strip() for tool in tools_part.split(',')]
            return tools
        return []

    def _score_template(self, candidate: TemplateCandidate, job_data: Dict[str, Any],
                       profile_type: str) -> Tuple[float, List[str]]:
        """
        Score a template candidate based on job requirements

        Returns:
            Tuple of (score, reasons_list)
        """
        score = 0.0
        reasons = []

        # Handle both dict and JobData object formats
        if hasattr(job_data, 'job_title_original'):
            # It's a JobData object
            job_title = getattr(job_data, 'job_title_original', '').lower()
            job_skills = set(getattr(job_data, 'skills', []))
            job_software = set(getattr(job_data, 'software', []))
        else:
            # It's a dict
            job_title = job_data.get('job_title_original', '').lower()
            job_skills = set(job_data.get('skills', []))
            job_software = set(job_data.get('software', []))

        # 1. Role matching (40% weight)
        role_score = self._calculate_role_score(candidate.role, job_title, profile_type)
        score += role_score * 0.4
        if role_score > 0.7:
            reasons.append(f"Role match: {candidate.role}")

        # 2. Skills/Tools matching (35% weight)
        skills_score = self._calculate_skills_score(candidate.tools, job_skills, job_software)
        score += skills_score * 0.35
        if skills_score > 0.5:
            reasons.append(f"Skills match: {', '.join(candidate.tools[:3])}")

        # 3. Specialization alignment (15% weight)
        spec_score = self._calculate_specialization_score(candidate.specialization, job_title)
        score += spec_score * 0.15
        if spec_score > 0.8:
            reasons.append(f"Specialization: {candidate.specialization}")

        # 4. Recency bonus (10% weight) - newer templates get slight preference
        recency_score = self._calculate_recency_score(candidate.file_date)
        score += recency_score * 0.1
        if recency_score > 0.5:
            reasons.append("Recent template")

        return score, reasons

    def _calculate_role_score(self, template_role: str, job_title: str, profile_type: str) -> float:
        """Calculate how well the template role matches the job"""
        job_lower = job_title.lower()

        # Exact role matching with higher priority
        if 'product analyst' in job_lower and template_role == 'PA':
            return 1.0
        elif 'data analyst' in job_lower and template_role == 'DA':
            return 1.0
        elif 'product manager' in job_lower and template_role == 'PM':
            return 1.0
        elif 'product owner' in job_lower and template_role == 'PO':
            return 1.0
        elif 'project manager' in job_lower and template_role == 'PJM':
            return 1.0
        elif 'business analyst' in job_lower and template_role == 'BA':
            return 1.0
        elif 'operations manager' in job_lower and template_role == 'OM':
            return 1.0

        # Profile type matching (fallback)
        expected_roles = self.role_mappings.get(profile_type, [])
        if template_role in expected_roles:
            return 0.8

        # Similar role matching with lower scores
        if template_role == 'PA' and any(word in job_lower for word in ['analyst', 'analysis', 'product']):
            return 0.6
        elif template_role == 'DA' and any(word in job_lower for word in ['data', 'analytics', 'analyst']):
            return 0.6
        elif template_role in ['PM', 'PO'] and 'product' in job_lower:
            return 0.6
        elif template_role == 'PJM' and 'manager' in job_lower:
            return 0.6

        # Very low score for completely different roles
        return 0.1

    def _calculate_skills_score(self, template_tools: List[str], job_skills: set, job_software: set) -> float:
        """Calculate skills/tools overlap score"""
        if not template_tools:
            return 0.0

        template_tools_lower = set(tool.lower() for tool in template_tools)
        job_skills_lower = set(skill.lower() for skill in job_skills)
        job_software_lower = set(soft.lower() for soft in job_software)

        # Combine job requirements
        job_all = job_skills_lower | job_software_lower

        if not job_all:
            return 0.5  # Neutral score if no job requirements specified

        # Calculate overlap
        overlap = template_tools_lower & job_all
        overlap_ratio = len(overlap) / len(job_all)

        # Bonus for having multiple matching tools
        if len(overlap) >= 2:
            overlap_ratio += 0.2

        return min(overlap_ratio, 1.0)

    def _calculate_specialization_score(self, template_spec: str, job_title: str) -> float:
        """Calculate specialization alignment score"""
        job_lower = job_title.lower()

        # Analytics/data focused jobs
        if any(word in job_lower for word in ['analytics', 'data', 'sql', 'tableau', 'python']):
            if template_spec in ['ANAL', 'AIML', 'ANDE', 'ANCO']:
                return 1.0
            elif template_spec == 'GEN':
                return 0.6

        # Technical/development jobs
        elif any(word in job_lower for word in ['code', 'development', 'engineering']):
            if template_spec in ['CODE', 'AIML']:
                return 1.0
            elif template_spec == 'GEN':
                return 0.6

        # General/business jobs
        else:
            if template_spec == 'GEN':
                return 0.8
            else:
                return 0.4  # Other specializations might still be relevant

        return 0.0

    def _calculate_recency_score(self, file_date: Optional[datetime]) -> float:
        """Calculate recency score (newer = higher score)"""
        if not file_date:
            return 0.0

        days_old = (datetime.now() - file_date).days

        if days_old <= 7:  # Very recent
            return 1.0
        elif days_old <= 30:  # Recent
            return 0.8
        elif days_old <= 90:  # Somewhat recent
            return 0.6
        else:  # Older
            return 0.3

    def get_template_info(self, template_path: Path) -> Dict[str, Any]:
        """Extract information about a specific template"""
        if not template_path.exists():
            return {}

        # Parse filename
        filename = template_path.name
        cv_pattern = re.compile(r'PedroHerrera_([A-Z]+)_([A-Z]+)_([A-Z]+)_(\d{4})\.docx$')
        match = cv_pattern.match(filename)

        if match:
            role_prefix, spec_prefix, model_prefix, year = match.groups()
            return {
                'filename': filename,
                'role': role_prefix,
                'specialization': spec_prefix,
                'business_model': model_prefix,
                'year': year,
                'folder': template_path.parent.name
            }

        return {'filename': filename}
