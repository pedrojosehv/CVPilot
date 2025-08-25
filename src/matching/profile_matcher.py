"""
Profile matching module for CVPilot
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from difflib import SequenceMatcher

from ..utils.models import JobData, MatchResult, ProfileType, ProfileConfig
from ..utils.logger import LoggerMixin

class ProfileMatcher(LoggerMixin):
    """Match job descriptions with profile configurations"""
    
    def __init__(self, profiles_path: Path):
        super().__init__()
        self.profiles_path = profiles_path
        self.profiles_cache: Dict[str, ProfileConfig] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load all profile configurations"""
        profile_files = list(self.profiles_path.glob("*.json"))
        
        for profile_file in profile_files:
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                profile_config = ProfileConfig(**profile_data)
                self.profiles_cache[profile_config.profile_id] = profile_config
                self.log_info(f"Loaded profile: {profile_config.name}")
                
            except Exception as e:
                self.log_error(f"Error loading profile {profile_file}: {str(e)}")
    
    def match_job_to_profile(self, job_data: JobData, profile_type: str) -> MatchResult:
        """Match job data to a specific profile type"""
        
        if profile_type not in self.profiles_cache:
            self.log_warning(f"Profile type {profile_type} not found, using default")
            profile_type = "product_management"
        
        profile = self.profiles_cache[profile_type]
        
        # Calculate skill matching
        matched_skills, missing_skills = self._match_skills(job_data.skills, profile.skills)
        
        # Calculate software matching
        matched_software, missing_software = self._match_software(job_data.software, profile.software)
        
        # Calculate fit score
        fit_score = self._calculate_fit_score(
            matched_skills, missing_skills,
            matched_software, missing_software,
            job_data, profile
        )
        
        # Generate gap list
        gap_list = self._generate_gap_list(missing_skills, missing_software, job_data, profile)
        
        # Calculate confidence
        confidence = self._calculate_confidence(fit_score, len(matched_skills), len(matched_software))
        
        return MatchResult(
            fit_score=fit_score,
            gap_list=gap_list,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            matched_software=matched_software,
            missing_software=missing_software,
            profile_type=ProfileType(profile_type),
            confidence=confidence
        )
    
    def _match_skills(self, job_skills: List[str], profile_skills: List[str]) -> tuple[List[str], List[str]]:
        """Match job skills with profile skills"""
        matched = []
        missing = []
        
        job_skills_lower = [skill.lower().strip() for skill in job_skills]
        profile_skills_lower = [skill.lower().strip() for skill in profile_skills]
        
        for profile_skill in profile_skills:
            profile_skill_lower = profile_skill.lower().strip()
            
            # Exact match
            if profile_skill_lower in job_skills_lower:
                matched.append(profile_skill)
                continue
            
            # Fuzzy match
            best_match = None
            best_ratio = 0
            
            for job_skill in job_skills:
                ratio = SequenceMatcher(None, profile_skill_lower, job_skill.lower().strip()).ratio()
                if ratio > 0.8 and ratio > best_ratio:  # 80% similarity threshold
                    best_match = profile_skill
                    best_ratio = ratio
            
            if best_match:
                matched.append(best_match)
            else:
                missing.append(profile_skill)
        
        return matched, missing
    
    def _match_software(self, job_software: List[str], profile_software: List[str]) -> tuple[List[str], List[str]]:
        """Match job software with profile software"""
        matched = []
        missing = []
        
        job_software_lower = [sw.lower().strip() for sw in job_software]
        profile_software_lower = [sw.lower().strip() for sw in profile_software]
        
        for profile_sw in profile_software:
            profile_sw_lower = profile_sw.lower().strip()
            
            # Exact match
            if profile_sw_lower in job_software_lower:
                matched.append(profile_sw)
                continue
            
            # Fuzzy match
            best_match = None
            best_ratio = 0
            
            for job_sw in job_software:
                ratio = SequenceMatcher(None, profile_sw_lower, job_sw.lower().strip()).ratio()
                if ratio > 0.8 and ratio > best_ratio:  # 80% similarity threshold
                    best_match = profile_sw
                    best_ratio = ratio
            
            if best_match:
                matched.append(best_match)
            else:
                missing.append(profile_sw)
        
        return matched, missing
    
    def _calculate_fit_score(self, 
                           matched_skills: List[str], 
                           missing_skills: List[str],
                           matched_software: List[str], 
                           missing_software: List[str],
                           job_data: JobData, 
                           profile: ProfileConfig) -> float:
        """Calculate overall fit score"""
        
        # Skill weight: 60%
        skill_score = len(matched_skills) / len(profile.skills) if profile.skills else 0
        
        # Software weight: 30%
        software_score = len(matched_software) / len(profile.software) if profile.software else 0
        
        # Seniority match weight: 10%
        seniority_score = self._calculate_seniority_match(job_data, profile)
        
        # Calculate weighted score
        fit_score = (skill_score * 0.6) + (software_score * 0.3) + (seniority_score * 0.1)
        
        return min(fit_score, 1.0)  # Cap at 1.0
    
    def _calculate_seniority_match(self, job_data: JobData, profile: ProfileConfig) -> float:
        """Calculate seniority level match"""
        if not job_data.seniority or not profile.seniority_level:
            return 0.5  # Neutral score if missing data
        
        # Simple mapping for now
        seniority_levels = {
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "manager": 5,
            "director": 6
        }
        
        job_level = seniority_levels.get(job_data.seniority.lower(), 2)
        profile_level = seniority_levels.get(profile.seniority_level.lower(), 2)
        
        # Calculate similarity (closer levels = higher score)
        level_diff = abs(job_level - profile_level)
        if level_diff == 0:
            return 1.0
        elif level_diff == 1:
            return 0.8
        elif level_diff == 2:
            return 0.6
        else:
            return 0.3
    
    def _generate_gap_list(self, 
                          missing_skills: List[str], 
                          missing_software: List[str],
                          job_data: JobData, 
                          profile: ProfileConfig) -> List[str]:
        """Generate list of gaps for improvement"""
        gaps = []
        
        # Add missing skills
        if missing_skills:
            gaps.append(f"Missing key skills: {', '.join(missing_skills[:5])}")
        
        # Add missing software
        if missing_software:
            gaps.append(f"Missing software tools: {', '.join(missing_software[:3])}")
        
        # Add seniority gap if applicable
        if job_data.seniority and profile.seniority_level:
            if job_data.seniority.lower() != profile.seniority_level.lower():
                gaps.append(f"Seniority mismatch: job requires {job_data.seniority}, profile is {profile.seniority_level}")
        
        # Add experience gap if applicable
        if job_data.experience_years and profile.experience_years:
            if job_data.experience_years != profile.experience_years:
                gaps.append(f"Experience mismatch: job requires {job_data.experience_years}, profile has {profile.experience_years}")
        
        return gaps
    
    def _calculate_confidence(self, fit_score: float, matched_skills_count: int, matched_software_count: int) -> float:
        """Calculate confidence in the match result"""
        # Base confidence on fit score
        confidence = fit_score
        
        # Adjust based on number of matches
        if matched_skills_count >= 10:
            confidence += 0.1
        elif matched_skills_count >= 5:
            confidence += 0.05
        
        if matched_software_count >= 5:
            confidence += 0.1
        elif matched_software_count >= 3:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile types"""
        return list(self.profiles_cache.keys())
    
    def get_profile_info(self, profile_type: str) -> Optional[ProfileConfig]:
        """Get profile configuration by type"""
        return self.profiles_cache.get(profile_type)
    
    def calculate_final_fit_score(self, job_data: JobData, profile_type: str, 
                                 replacements: 'Replacements') -> Dict[str, Any]:
        """Calculate final fit score after CV improvements"""
        
        self.log_info("Calculating final fit score after CV improvements")
        
        # Get initial match
        initial_match = self.match_job_to_profile(job_data, profile_type)
        
        # Extract skills and software from generated content
        generated_skills = self._extract_skills_from_content(replacements.skill_list.content)
        generated_software = self._extract_software_from_content(replacements.software_list.content)
        
        # Calculate improved skill match
        improved_skill_match = self._match_skills(job_data.skills, generated_skills)
        
        # Calculate improved software match
        improved_software_match = self._match_software(job_data.software, generated_software)
        
        # Calculate final fit score using the same method as initial
        profile = self.profiles_cache.get(profile_type, self.profiles_cache.get("product_management"))
        final_fit_score = self._calculate_fit_score(
            improved_skill_match[0], improved_skill_match[1],
            improved_software_match[0], improved_software_match[1],
            job_data, profile
        )
        
        # Calculate improvement metrics
        skill_improvement = len(improved_skill_match[0]) - len(initial_match.matched_skills)
        software_improvement = len(improved_software_match[0]) - len(initial_match.matched_software)
        overall_improvement = final_fit_score - initial_match.fit_score
        
        return {
            'initial_fit_score': initial_match.fit_score,
            'final_fit_score': final_fit_score,
            'improvement': overall_improvement,
            'skill_improvement': skill_improvement,
            'software_improvement': software_improvement,
            'initial_matched_skills': initial_match.matched_skills,
            'final_matched_skills': improved_skill_match[0],
            'initial_matched_software': initial_match.matched_software,
            'final_matched_software': improved_software_match[0],
            'new_skills_added': list(set(improved_skill_match[0]) - set(initial_match.matched_skills)),
            'new_software_added': list(set(improved_software_match[0]) - set(initial_match.matched_software))
        }
    
    def _extract_skills_from_content(self, content) -> List[str]:
        """Extract skills from generated content"""
        if not content:
            return []
        
        # Handle both string and list content
        if isinstance(content, list):
            return [skill.strip() for skill in content if skill.strip() and len(skill.strip()) > 2]
        
        # Split by common separators and clean up
        skills = []
        for skill in content.split(','):
            skill = skill.strip()
            if skill and len(skill) > 2:  # Filter out very short items
                skills.append(skill)
        
        return skills
    
    def _extract_software_from_content(self, content) -> List[str]:
        """Extract software from generated content"""
        if not content:
            return []
        
        # Handle both string and list content
        if isinstance(content, list):
            return [sw.strip() for sw in content if sw.strip() and len(sw.strip()) > 2]
        
        # Split by common separators and clean up
        software = []
        for sw in content.split(','):
            sw = sw.strip()
            if sw and len(sw) > 2:  # Filter out very short items
                software.append(sw)
        
        return software
