"""
Database Profile Selector - Selects best CV profile from role database instead of DOCX files
CVPilot - Uses role-categorized database to find optimal profile for job requirements
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re

from .logger import LoggerMixin
from .role_content_manager import RoleContentManager
from .models import JobData


class DatabaseProfileSelector(LoggerMixin):
    """Selects optimal CV profile from role database"""

    def __init__(self, role_manager: RoleContentManager = None):
        super().__init__()
        self.role_manager = role_manager or RoleContentManager()
        
        # Job title to role mapping
        self.job_title_to_role = {
            # Product roles
            'product manager': 'Product Manager',
            'senior product manager': 'Product Manager',
            'product management': 'Product Manager',
            'pm': 'Product Manager',
            
            'product analyst': 'Product Analyst',
            'senior product analyst': 'Product Analyst',
            'product analytics': 'Product Analyst',
            'pa': 'Product Analyst',
            
            'product owner': 'Product Owner',
            'senior product owner': 'Product Owner',
            'po': 'Product Owner',
            
            'product operations': 'Product Operations Specialist',
            'product ops': 'Product Operations Specialist',
            
            # Business roles
            'business analyst': 'Business Analyst',
            'senior business analyst': 'Business Analyst',
            'business analysis': 'Business Analyst',
            'ba': 'Business Analyst',
            
            # Data roles
            'data analyst': 'Data Analyst',
            'senior data analyst': 'Data Analyst',
            'data analytics': 'Data Analyst',
            'business intelligence analyst': 'Data Analyst',
            'bi analyst': 'Data Analyst',
            'da': 'Data Analyst',
            
            # Project roles
            'project manager': 'Project Manager',
            'senior project manager': 'Project Manager',
            'project management': 'Project Manager',
            'pjm': 'Project Manager',
            
            # Quality roles
            'quality analyst': 'Quality Analyst',
            'quality assurance analyst': 'Quality Assurance Analyst',
            'qa analyst': 'Quality Assurance Analyst',
            'qaa': 'Quality Assurance Analyst'
        }
        
        # Skills that indicate specific roles
        self.role_skills_indicators = {
            'Product Manager': ['roadmap', 'strategy', 'stakeholder', 'product development', 'go-to-market'],
            'Product Analyst': ['analytics', 'metrics', 'kpi', 'dashboard', 'product metrics', 'user behavior'],
            'Business Analyst': ['requirements', 'process', 'workflow', 'documentation', 'business process'],
            'Data Analyst': ['sql', 'python', 'tableau', 'power bi', 'data visualization', 'statistics'],
            'Project Manager': ['gantt', 'timeline', 'milestone', 'resource management', 'project planning'],
            'Product Owner': ['agile', 'scrum', 'user stories', 'backlog', 'sprint planning']
        }

    def select_best_profile(self, job_data: JobData) -> Dict[str, Any]:
        """
        Select best CV profile from database based on job requirements
        
        Returns:
            Dict with selected profile data and metadata
        """
        self.logger.info(f"🎯 Selecting best profile for: {job_data.job_title_original}")
        
        # 1. Direct role matching from job title
        primary_role = self._extract_role_from_job_title(job_data.job_title_original)
        
        # 2. Skills-based role detection
        skills_roles = self._detect_roles_from_skills(job_data.skills + job_data.software)
        
        # 3. Get candidate roles with scores
        candidate_roles = self._score_candidate_roles(primary_role, skills_roles, job_data)
        
        # 4. Select best role and get its profile
        best_role, best_score = self._select_best_role(candidate_roles)
        
        if not best_role:
            self.logger.warning("❌ No suitable role found, using fallback")
            return self._get_fallback_profile(job_data)
        
        # 5. Get complete profile data from database
        profile_data = self._get_role_profile_data(best_role, job_data)
        
        self.logger.info(f"✅ Selected profile: {best_role} (score: {best_score:.2f})")
        
        return {
            'selected_role': best_role,
            'confidence_score': best_score,
            'profile_data': profile_data,
            'selection_reasoning': {
                'primary_role': primary_role,
                'skills_roles': skills_roles,
                'candidate_scores': candidate_roles
            }
        }

    def _extract_role_from_job_title(self, job_title: str) -> Optional[str]:
        """Extract role from job title using mapping"""
        job_title_clean = job_title.lower().strip()
        
        # Direct mapping
        if job_title_clean in self.job_title_to_role:
            return self.job_title_to_role[job_title_clean]
        
        # Partial matching
        for title_pattern, role in self.job_title_to_role.items():
            if title_pattern in job_title_clean:
                return role
        
        return None

    def _detect_roles_from_skills(self, skills: List[str]) -> Dict[str, float]:
        """Detect possible roles from skills with confidence scores"""
        role_scores = {}
        
        skills_lower = [skill.lower() for skill in skills]
        
        for role, role_skills in self.role_skills_indicators.items():
            score = 0
            matches = 0
            
            for skill in skills_lower:
                for role_skill in role_skills:
                    if role_skill.lower() in skill:
                        score += 1
                        matches += 1
                        break
            
            if matches > 0:
                # Normalize score
                role_scores[role] = min(score / len(role_skills), 1.0)
        
        return role_scores

    def _score_candidate_roles(self, primary_role: Optional[str], 
                             skills_roles: Dict[str, float], 
                             job_data: JobData) -> Dict[str, float]:
        """Score all candidate roles"""
        candidate_scores = {}
        
        # Primary role from title gets high base score
        if primary_role:
            candidate_scores[primary_role] = 0.8
        
        # Add skills-based scores
        for role, skill_score in skills_roles.items():
            current_score = candidate_scores.get(role, 0)
            candidate_scores[role] = max(current_score, skill_score * 0.6)
        
        # Boost score if role exists in database with good content
        for role in candidate_scores.keys():
            role_content = self.role_manager.get_role_content(role)
            if role_content and role_content.cv_count > 0:
                # Boost based on available content
                content_boost = min(role_content.cv_count * 0.1, 0.3)
                candidate_scores[role] += content_boost
                
                # Boost based on success metrics
                avg_success = role_content.success_metrics.get('fit_scores', [0])
                if avg_success:
                    success_boost = (sum(avg_success) / len(avg_success)) * 0.2
                    candidate_scores[role] += success_boost
        
        return candidate_scores

    def _select_best_role(self, candidate_scores: Dict[str, float]) -> Tuple[Optional[str], float]:
        """Select the best role from candidates"""
        if not candidate_scores:
            return None, 0.0
        
        best_role = max(candidate_scores, key=candidate_scores.get)
        best_score = candidate_scores[best_role]
        
        return best_role, best_score

    def _get_role_profile_data(self, role: str, job_data: JobData) -> Dict[str, Any]:
        """Get complete profile data for selected role"""
        role_content = self.role_manager.get_role_content(role)
        
        if not role_content:
            self.logger.warning(f"⚠️ No content found for role: {role}")
            return self._create_empty_profile(role)
        
        # Get best content for this job
        best_summary = self._select_best_summary(role_content.summaries, job_data)
        best_bullets = self._select_best_bullets(role_content.bullet_points, job_data)
        relevant_skills = self._select_relevant_skills(role_content.skills, job_data)
        relevant_software = self._select_relevant_software(role_content.software, job_data)
        
        return {
            'role': role,
            'summary': best_summary,
            'bullet_points': best_bullets,
            'skills': relevant_skills,
            'software': relevant_software,
            'achievements': role_content.achievements[:5],  # Top 5 achievements
            'cv_count': role_content.cv_count,
            'last_updated': role_content.last_updated,
            'success_metrics': role_content.success_metrics
        }

    def _select_best_summary(self, summaries: List[str], job_data: JobData) -> str:
        """Select best summary for job requirements"""
        if not summaries:
            return ""
        
        # For now, return the most recent (last) summary
        # TODO: Implement similarity matching based on job requirements
        return summaries[-1] if summaries else ""

    def _select_best_bullets(self, bullets: List[str], job_data: JobData, limit: int = 5) -> List[str]:
        """Select best bullet points for job requirements"""
        if not bullets:
            return []
        
        # Simple selection - return last bullets (most recent)
        # TODO: Implement relevance scoring based on job requirements
        return bullets[-limit:] if len(bullets) >= limit else bullets

    def _select_relevant_skills(self, skills: List[str], job_data: JobData) -> List[str]:
        """Select most relevant skills"""
        if not skills:
            return []
        
        job_skills = set(skill.lower() for skill in job_data.skills)
        
        # Prioritize skills that match job requirements
        matching_skills = []
        other_skills = []
        
        for skill in skills:
            if skill.lower() in job_skills:
                matching_skills.append(skill)
            else:
                other_skills.append(skill)
        
        # Return matching skills first, then others
        return matching_skills + other_skills[:10-len(matching_skills)]

    def _select_relevant_software(self, software: List[str], job_data: JobData) -> List[str]:
        """Select most relevant software"""
        if not software:
            return []
        
        job_software = set(tool.lower() for tool in job_data.software)
        
        # Prioritize software that matches job requirements
        matching_software = []
        other_software = []
        
        for tool in software:
            if tool.lower() in job_software:
                matching_software.append(tool)
            else:
                other_software.append(tool)
        
        # Return matching software first, then others
        return matching_software + other_software[:8-len(matching_software)]

    def _get_fallback_profile(self, job_data: JobData) -> Dict[str, Any]:
        """Get fallback profile when no good match found"""
        self.logger.warning("🔄 Using fallback profile selection")
        
        # Try to find any available profile
        database_summary = self.role_manager.get_database_summary()
        
        if database_summary['total_roles'] > 0:
            # Use the role with most content
            best_role = max(database_summary['roles_by_content'].items(), 
                          key=lambda x: x[1]['cv_count'])[0]
            
            return {
                'selected_role': best_role,
                'confidence_score': 0.3,  # Low confidence
                'profile_data': self._get_role_profile_data(best_role, job_data),
                'selection_reasoning': {
                    'fallback': True,
                    'reason': 'No direct match found, using most complete profile'
                }
            }
        
        return {
            'selected_role': 'Generic',
            'confidence_score': 0.1,
            'profile_data': self._create_empty_profile('Generic'),
            'selection_reasoning': {
                'fallback': True,
                'reason': 'No profiles in database'
            }
        }

    def _create_empty_profile(self, role: str) -> Dict[str, Any]:
        """Create empty profile structure"""
        return {
            'role': role,
            'summary': '',
            'bullet_points': [],
            'skills': [],
            'software': [],
            'achievements': [],
            'cv_count': 0,
            'last_updated': '',
            'success_metrics': {}
        }

    def get_available_roles(self) -> List[Dict[str, Any]]:
        """Get list of available roles in database"""
        database_summary = self.role_manager.get_database_summary()
        
        roles = []
        for role_name, content_data in database_summary['roles_by_content'].items():
            roles.append({
                'role': role_name,
                'cv_count': content_data['cv_count'],
                'content_richness': {
                    'summaries': content_data['summaries'],
                    'bullet_points': content_data['bullet_points'],
                    'skills': content_data['skills'],
                    'software': content_data['software'],
                    'achievements': content_data['achievements']
                },
                'avg_success_score': content_data['avg_success_score']
            })
        
        # Sort by content richness and success
        roles.sort(key=lambda x: (x['cv_count'], x['avg_success_score']), reverse=True)
        
        return roles

