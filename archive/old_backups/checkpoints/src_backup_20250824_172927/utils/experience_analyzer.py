"""
Experience Analyzer for CVPilot
Uses LLM to analyze work experience from CV templates
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from .api_key_manager import get_api_key, mark_api_error
from .logger import LoggerMixin

class ExperienceAnalyzer(LoggerMixin):
    """Analyzes work experience from CV templates using LLM"""
    
    def __init__(self):
        super().__init__()
        
    def analyze_experience_section(self, experience_text: str) -> List[Dict[str, Any]]:
        """Analyze experience section and extract structured information"""
        
        if not experience_text:
            return []
        
        # Create prompt for LLM analysis
        prompt = self._create_experience_analysis_prompt(experience_text)
        
        try:
            # Call LLM for intelligent analysis
            response = self._call_llm(prompt)
            
            # Parse LLM response
            experiences = self._parse_experience_response(response)
            
            self.log_info(f"✅ Analyzed {len(experiences)} work experiences")
            return experiences
            
        except Exception as e:
            self.log_error(f"Experience analysis failed: {e}")
            # Fallback to regex parsing
            return self._fallback_experience_parsing(experience_text)
    
    def _create_experience_analysis_prompt(self, experience_text: str) -> str:
        """Create prompt for experience analysis"""
        
        prompt = f"""
        You are an expert CV analyst. Analyze this work experience section and extract structured information.

        EXPERIENCE TEXT:
        {experience_text}

        ANALYSIS REQUIREMENTS:
        1. Identify each work experience entry
        2. Extract the following information for each:
           - Company name
           - Location (City, Country)
           - Job title(s) - if multiple roles separated by "|", select the most relevant one
           - Date range (start - end)
           - Specialization/industry focus
        3. Handle role formats like: "Role 1 | Role 2 | ... | Role N (Specialization)"
        4. Select the most relevant role based on context and industry alignment

        RESPONSE FORMAT:
        Return ONLY a JSON array with this structure:
        [
            {{
                "company": "Company Name",
                "location": "City, Country",
                "job_title": "Selected Job Title",
                "date_range": "MM/YYYY - MM/YYYY",
                "specialization": "Industry/Specialization focus",
                "original_text": "Original text for this experience"
            }}
        ]

        Analyze the experience section and extract structured information:
        """
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for experience analysis"""
        import openai
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get API key from manager
                api_key = get_api_key("round_robin")
                if not api_key:
                    raise ValueError("No API key available")
                
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert CV analyst. Extract precise, structured information from work experience sections."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=1500
                )
                return response.choices[0].message.content
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit errors
                if any(keyword in error_msg for keyword in ['rate limit', 'quota', 'too many requests']):
                    self.log_warning(f"Rate limit hit on attempt {attempt + 1}, rotating API key...")
                    mark_api_error(api_key, "rate_limit")
                    continue
                
                # Check for API key errors
                elif any(keyword in error_msg for keyword in ['invalid api key', 'authentication', 'unauthorized']):
                    self.log_error(f"API key error: {e}")
                    mark_api_error(api_key, "invalid_key")
                    continue
                
                # Other errors
                else:
                    self.log_error(f"LLM call failed: {e}")
                    if attempt == max_retries - 1:
                        break
                    continue
        
        # If all retries failed, return empty response
        return '[]'
    
    def _parse_experience_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract experience information"""
        import json
        
        try:
            # Try to parse JSON response
            experiences = json.loads(response)
            
            if not isinstance(experiences, list):
                self.log_error("LLM response is not a list")
                return []
            
            # Validate each experience entry
            valid_experiences = []
            for exp in experiences:
                if isinstance(exp, dict) and 'company' in exp and 'job_title' in exp:
                    valid_experiences.append(exp)
            
            return valid_experiences
            
        except json.JSONDecodeError:
            self.log_error("Failed to parse LLM response as JSON")
            return []
    
    def _fallback_experience_parsing(self, experience_text: str) -> List[Dict[str, Any]]:
        """Fallback experience parsing using regex"""
        experiences = []
        
        # Split by potential company headers
        lines = experience_text.split('\n')
        current_experience = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for company header pattern: "Company — City, Country"
            if "—" in line and ("," in line or "Remote" in line):
                # Save previous experience
                if current_experience:
                    experiences.append(current_experience)
                
                # Start new experience
                parts = line.split("—")
                if len(parts) >= 2:
                    company = parts[0].strip()
                    location = parts[1].strip()
                    current_experience = {
                        "company": company,
                        "location": location,
                        "job_title": "Unknown",
                        "date_range": "Unknown",
                        "specialization": "Unknown",
                        "original_text": line
                    }
            
            # Check for job title and date pattern
            elif "(" in line and ")" in line and any(month in line for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                # Extract job title and dates
                title_match = re.search(r'([^(]+)\s*\(([^)]+)\)', line)
                if title_match:
                    job_title = title_match.group(1).strip()
                    date_info = title_match.group(2).strip()
                    
                    if current_experience:
                        current_experience["job_title"] = job_title
                        current_experience["date_range"] = date_info
                        current_experience["original_text"] += f"\n{line}"
        
        # Add last experience
        if current_experience:
            experiences.append(current_experience)
        
        return experiences
    
    def select_most_relevant_role(self, roles_text: str, target_job: Dict[str, Any]) -> str:
        """Select the most relevant role from a multi-role format"""
        
        if "|" not in roles_text:
            return roles_text.strip()
        
        # Split roles
        roles = [role.strip() for role in roles_text.split("|")]
        
        # Create prompt for role selection
        prompt = f"""
        Select the most relevant role for this job opportunity from the provided options.

        TARGET JOB:
        - Title: {target_job.get('job_title_original', 'Unknown')}
        - Company: {target_job.get('company', 'Unknown')}
        - Required Skills: {', '.join(target_job.get('skills', [])[:10])}
        - Required Software: {', '.join(target_job.get('software', [])[:5])}
        - Seniority: {target_job.get('seniority', 'Unknown')}

        AVAILABLE ROLES:
        {chr(10).join([f"{i+1}. {role}" for i, role in enumerate(roles)])}

        REQUIREMENTS:
        1. Select ONLY ONE role that best aligns with the target job
        2. Consider:
           - Industry relevance
           - Skill alignment
           - Seniority match
           - Technical focus
        3. Return ONLY the selected role text

        Selected role:
        """
        
        try:
            response = self._call_llm(prompt)
            selected_role = response.strip()
            
            # Validate the selected role exists in the original list
            for role in roles:
                if selected_role.lower() in role.lower() or role.lower() in selected_role.lower():
                    return role
            
            # If no match found, return the first role
            return roles[0]
            
        except Exception as e:
            self.log_error(f"Role selection failed: {e}")
            return roles[0]  # Return first role as fallback
