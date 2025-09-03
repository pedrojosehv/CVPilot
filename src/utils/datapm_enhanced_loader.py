"""
Enhanced DataPM Loader - Complete integration with scrapped and csv_processed data
CVPilot - Loads job descriptions from scrapped folder and skills data from csv_processed
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

from .logger import LoggerMixin
from .models import JobData


class EnhancedDataPMLoader(LoggerMixin):
    """Enhanced loader for complete DataPM integration"""

    def __init__(self, datapm_base_path: str = None):
        super().__init__()
        
        # Set up paths
        if datapm_base_path:
            self.datapm_path = Path(datapm_base_path)
        else:
            # Default paths
            self.datapm_path = Path("D:/Work Work/Upwork/DataPM")
        
        self.scrapped_path = self.datapm_path / "csv" / "src" / "scrapped"
        self.csv_processed_path = self.datapm_path / "csv" / "src" / "csv_processed"
        
        # Verify paths exist
        self._verify_paths()
        
        self.logger.info(f"✅ Enhanced DataPM Loader initialized")
        self.logger.info(f"📂 Scrapped path: {self.scrapped_path}")
        self.logger.info(f"📊 CSV processed path: {self.csv_processed_path}")

    def _verify_paths(self):
        """Verify that required DataPM paths exist"""
        if not self.datapm_path.exists():
            self.logger.warning(f"⚠️ DataPM base path not found: {self.datapm_path}")
        
        if not self.scrapped_path.exists():
            self.logger.warning(f"⚠️ Scrapped path not found: {self.scrapped_path}")
        
        if not self.csv_processed_path.exists():
            self.logger.warning(f"⚠️ CSV processed path not found: {self.csv_processed_path}")

    def get_complete_job_data(self, job_id: str) -> Dict[str, Any]:
        """
        Get complete job data including description from scrapped and skills from csv_processed
        
        Returns:
            Complete job data with description, skills summary, and metadata
        """
        self.logger.info(f"🔍 Loading complete job data for ID: {job_id}")
        
        # 1. Get basic job data (existing functionality)
        basic_job_data = self._get_basic_job_data(job_id)
        
        # 2. Get full job description from scrapped folder
        job_description = self._get_job_description_from_scrapped(job_id, basic_job_data)
        
        # 3. Get skills summary from csv_processed
        skills_summary = self._get_skills_summary_from_csv_processed(job_id, basic_job_data)
        
        # 4. Extract job title (short) for CV main title
        job_title_short = self._extract_short_job_title(basic_job_data.get('job_title_original', ''))
        
        # 5. Combine all data
        complete_data = {
            # Basic job data (required fields for JobData model)
            'job_id': job_id,
            'job_title_original': basic_job_data.get('job_title_original', ''),
            'job_title_short': basic_job_data.get('job_title_short', job_title_short),
            'company': basic_job_data.get('company', ''),
            'country': basic_job_data.get('country', 'Unknown'),
            'state': basic_job_data.get('state'),
            'city': basic_job_data.get('city'),
            'schedule_type': basic_job_data.get('schedule_type'),
            'experience_years': basic_job_data.get('experience_years'),
            'seniority': basic_job_data.get('seniority'),
            'skills': basic_job_data.get('skills', []),
            'degrees': basic_job_data.get('degrees', []),
            'software': basic_job_data.get('software', []),
            
            # Enhanced data from scrapped
            'job_description_full': job_description.get('full_description', ''),
            'job_description_summary': job_description.get('summary', ''),
            'role_context': job_description.get('role_context', ''),
            'company_context': job_description.get('company_context', ''),
            'requirements_detailed': job_description.get('requirements', []),
            
            # Enhanced data from csv_processed
            'skills_summary': skills_summary.get('skills_breakdown', {}),
            'software_summary': skills_summary.get('software_breakdown', {}),
            'skills_priority': skills_summary.get('priority_skills', []),
            'software_priority': skills_summary.get('priority_software', []),
            'role_alignment': skills_summary.get('role_alignment', {}),
            
            # Metadata
            'data_sources': {
                'basic_data': basic_job_data.get('source', 'manual_export'),
                'description_source': job_description.get('source', 'none'),
                'skills_source': skills_summary.get('source', 'none')
            },
            'processing_timestamp': job_description.get('timestamp', ''),
            'data_completeness': self._calculate_data_completeness(basic_job_data, job_description, skills_summary)
        }
        
        self.logger.info(f"✅ Complete job data loaded - completeness: {complete_data['data_completeness']:.1%}")
        
        return complete_data

    def _get_basic_job_data(self, job_id: str) -> Dict[str, Any]:
        """Get basic job data from manual export (existing functionality)"""
        try:
            # Try manual export first
            manual_export_file = Path("manual_exports/manual_export.csv")
            if manual_export_file.exists():
                # Try different encodings to handle encoding issues
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                
                for encoding in encodings:
                    try:
                        with open(manual_export_file, 'r', encoding=encoding) as f:
                            reader = csv.DictReader(f, delimiter=';')
                            for row in reader:
                                # Handle both string and integer job IDs
                                row_job_id = row.get('Job ID') or row.get('job_id')
                                if row_job_id and (str(row_job_id).strip() == str(job_id).strip()):
                                    # Handle both possible column name formats
                                    job_title_col = 'Job title (original)' if 'Job title (original)' in row else 'job_title_original'
                                    company_col = 'Company' if 'Company' in row else 'company'
                                    skills_col = 'Skills' if 'Skills' in row else 'skills'
                                    software_col = 'Software' if 'Software' in row else 'software'
                                    
                                    return {
                                        'job_id': job_id,
                                        'job_title_original': row.get(job_title_col, ''),
                                        'job_title_short': row.get('Job title (short)', row.get('job_title_short', '')),
                                        'company': row.get(company_col, ''),
                                        'country': row.get('Country', row.get('country', 'Unknown')),
                                        'state': row.get('State', row.get('state', None)),
                                        'city': row.get('City', row.get('city', None)),
                                        'schedule_type': row.get('Schedule type', row.get('schedule_type', None)),
                                        'experience_years': row.get('Experience years', row.get('experience_years', None)),
                                        'seniority': row.get('Seniority', row.get('seniority', None)),
                                        'skills': [s.strip() for s in row.get(skills_col, '').split(';')] if row.get(skills_col) else [],
                                        'degrees': [s.strip() for s in row.get('Degrees', row.get('degrees', '')).split(';')] if row.get('Degrees', row.get('degrees', '')) else [],
                                        'software': [s.strip() for s in row.get(software_col, '').split(';')] if row.get(software_col) else [],
                                        'source': 'manual_export'
                                    }
                        break  # If successful, exit the encoding loop
                    except UnicodeDecodeError:
                        continue  # Try next encoding
            
            # Fallback to empty data
            self.logger.warning(f"⚠️ No basic job data found for ID: {job_id}")
            return {
                'job_id': job_id,
                'job_title_original': '',
                'job_title_short': '',
                'company': '',
                'country': 'Unknown',
                'state': None,
                'city': None,
                'schedule_type': None,
                'experience_years': None,
                'seniority': None,
                'skills': [],
                'degrees': [],
                'software': [],
                'source': 'none'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error loading basic job data: {e}")
            return {}

    def _get_job_description_from_scrapped(self, job_id: str, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get full job description from scrapped folder"""
        try:
            if not self.scrapped_path.exists():
                return {'source': 'none'}
            
            # Look for job description files
            # Try different naming patterns
            possible_files = [
                f"job_{job_id}.json",
                f"{job_id}.json",
                f"job_description_{job_id}.json",
                f"{basic_data.get('company', '')}_{job_id}.json".replace(' ', '_'),
            ]
            
            for filename in possible_files:
                file_path = self.scrapped_path / filename
                if file_path.exists():
                    return self._parse_job_description_file(file_path)
            
            # If no specific file found, try to find by company or title matching
            company = basic_data.get('company', '').lower()
            job_title = basic_data.get('job_title_original', '').lower()
            
            for json_file in self.scrapped_path.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Check if this file matches our job
                    if self._matches_job_criteria(data, job_id, company, job_title):
                        return self._parse_job_description_data(data, str(json_file))
                        
                except Exception as e:
                    continue
            
            self.logger.warning(f"⚠️ No job description found in scrapped folder for ID: {job_id}")
            return {'source': 'none'}
            
        except Exception as e:
            self.logger.error(f"❌ Error loading job description from scrapped: {e}")
            return {'source': 'error', 'error': str(e)}

    def _parse_job_description_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse job description from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._parse_job_description_data(data, str(file_path))
            
        except Exception as e:
            self.logger.error(f"❌ Error parsing job description file {file_path}: {e}")
            return {'source': 'error', 'error': str(e)}

    def _parse_job_description_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Parse job description data from JSON"""
        
        # Extract full description
        full_description = data.get('job_description', data.get('description', ''))
        
        # Extract role context (responsibilities, duties)
        role_context = self._extract_role_context(full_description)
        
        # Extract company context
        company_context = self._extract_company_context(data, full_description)
        
        # Extract detailed requirements
        requirements = self._extract_requirements(full_description)
        
        # Create summary
        summary = self._create_description_summary(full_description, role_context)
        
        return {
            'full_description': full_description,
            'summary': summary,
            'role_context': role_context,
            'company_context': company_context,
            'requirements': requirements,
            'source': 'scrapped',
            'source_file': source,
            'timestamp': data.get('scraped_at', data.get('timestamp', ''))
        }

    def _extract_role_context(self, description: str) -> str:
        """Extract role-specific context from job description"""
        if not description:
            return ""
        
        # Look for sections that describe the role
        role_patterns = [
            r"(?i)(role|position|job)\s+(overview|description|summary):?\s*([^.]*\.)",
            r"(?i)(responsibilities|duties):?\s*([^.]*\.)",
            r"(?i)(what you.ll do|your role|key responsibilities):?\s*([^.]*\.)",
        ]
        
        role_context_parts = []
        
        for pattern in role_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if isinstance(match, tuple):
                    role_context_parts.append(match[-1].strip())
                else:
                    role_context_parts.append(match.strip())
        
        if role_context_parts:
            return " ".join(role_context_parts)
        
        # Fallback: take first paragraph if it seems role-related
        paragraphs = description.split('\n\n')
        for para in paragraphs[:3]:
            if any(keyword in para.lower() for keyword in ['role', 'position', 'responsible', 'duties']):
                return para.strip()
        
        return ""

    def _extract_company_context(self, data: Dict[str, Any], description: str) -> str:
        """Extract company context from job data"""
        company_parts = []
        
        # From structured data
        if 'company_description' in data:
            company_parts.append(data['company_description'])
        
        if 'company_size' in data:
            company_parts.append(f"Company size: {data['company_size']}")
        
        if 'industry' in data:
            company_parts.append(f"Industry: {data['industry']}")
        
        # From description text
        company_patterns = [
            r"(?i)(about us|about the company|company overview):?\s*([^.]*\.)",
            r"(?i)(we are|our company):?\s*([^.]*\.)",
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if isinstance(match, tuple):
                    company_parts.append(match[-1].strip())
        
        return " ".join(company_parts)

    def _extract_requirements(self, description: str) -> List[str]:
        """Extract detailed requirements from job description"""
        requirements = []
        
        # Look for requirements sections
        req_patterns = [
            r"(?i)(requirements|qualifications|skills|experience):?\s*([^.]*\.)",
            r"(?i)(must have|required|essential):?\s*([^.]*\.)",
        ]
        
        for pattern in req_patterns:
            matches = re.findall(pattern, description)
            for match in matches:
                if isinstance(match, tuple):
                    requirements.append(match[-1].strip())
        
        return requirements

    def _create_description_summary(self, full_description: str, role_context: str) -> str:
        """Create a summary of the job description"""
        if not full_description:
            return ""
        
        # Use role context if available, otherwise first paragraph
        if role_context:
            return role_context[:300] + "..." if len(role_context) > 300 else role_context
        
        # Fallback to first paragraph
        paragraphs = full_description.split('\n\n')
        if paragraphs:
            first_para = paragraphs[0].strip()
            return first_para[:300] + "..." if len(first_para) > 300 else first_para
        
        return full_description[:300] + "..." if len(full_description) > 300 else full_description

    def _matches_job_criteria(self, data: Dict[str, Any], job_id: str, company: str, job_title: str) -> bool:
        """Check if scraped data matches job criteria"""
        
        # Check job ID
        if 'job_id' in data and data['job_id'] == job_id:
            return True
        
        # Check company name
        if company and 'company' in data:
            if company.lower() in data['company'].lower():
                return True
        
        # Check job title
        if job_title and 'job_title' in data:
            if job_title.lower() in data['job_title'].lower():
                return True
        
        return False

    def _get_skills_summary_from_csv_processed(self, job_id: str, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get skills summary from csv_processed folder"""
        try:
            if not self.csv_processed_path.exists():
                return {'source': 'none'}
            
            # Look for processed CSV files
            csv_files = list(self.csv_processed_path.glob("*.csv"))
            
            for csv_file in csv_files:
                skills_data = self._search_skills_in_csv(csv_file, job_id, basic_data)
                if skills_data['source'] != 'none':
                    return skills_data
            
            self.logger.warning(f"⚠️ No skills data found in csv_processed for ID: {job_id}")
            return {'source': 'none'}
            
        except Exception as e:
            self.logger.error(f"❌ Error loading skills from csv_processed: {e}")
            return {'source': 'error', 'error': str(e)}

    def _search_skills_in_csv(self, csv_file: Path, job_id: str, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for skills data in specific CSV file"""
        try:
            # Try different encodings to handle encoding issues
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f, delimiter=';')
                        
                        for row in reader:
                            # Try to match by job_id first
                            if row.get('job_id') == job_id:
                                return self._parse_skills_row(row, str(csv_file))
                            
                            # Try to match by company and title
                            if self._row_matches_job(row, basic_data):
                                return self._parse_skills_row(row, str(csv_file))
                    
                    return {'source': 'none'}
                except UnicodeDecodeError:
                    continue  # Try next encoding
            
            return {'source': 'none'}
            
        except Exception as e:
            self.logger.error(f"❌ Error reading CSV file {csv_file}: {e}")
            return {'source': 'error', 'error': str(e)}

    def _row_matches_job(self, row: Dict[str, Any], basic_data: Dict[str, Any]) -> bool:
        """Check if CSV row matches job data"""
        company = basic_data.get('company', '').lower()
        job_title = basic_data.get('job_title_original', '').lower()
        
        row_company = row.get('company', '').lower()
        row_title = row.get('job_title', row.get('job_title_original', '')).lower()
        
        return (company and company in row_company) or (job_title and job_title in row_title)

    def _parse_skills_row(self, row: Dict[str, Any], source_file: str) -> Dict[str, Any]:
        """Parse skills data from CSV row"""
        
        # Extract skills breakdown
        skills_breakdown = {}
        software_breakdown = {}
        
        # Parse skills columns
        if 'skills' in row:
            skills_breakdown = self._parse_skills_string(row['skills'])
        
        if 'software' in row:
            software_breakdown = self._parse_skills_string(row['software'])
        
        # Extract priority skills
        priority_skills = self._extract_priority_items(skills_breakdown)
        priority_software = self._extract_priority_items(software_breakdown)
        
        # Calculate role alignment
        role_alignment = self._calculate_role_alignment(skills_breakdown, software_breakdown)
        
        return {
            'skills_breakdown': skills_breakdown,
            'software_breakdown': software_breakdown,
            'priority_skills': priority_skills,
            'priority_software': priority_software,
            'role_alignment': role_alignment,
            'source': 'csv_processed',
            'source_file': source_file
        }

    def _parse_skills_string(self, skills_str: str) -> Dict[str, int]:
        """Parse skills string into breakdown with counts"""
        if not skills_str:
            return {}
        
        skills = [skill.strip() for skill in skills_str.split(',')]
        skills_count = {}
        
        for skill in skills:
            if skill:
                skills_count[skill] = skills_count.get(skill, 0) + 1
        
        return skills_count

    def _extract_priority_items(self, items_dict: Dict[str, int]) -> List[str]:
        """Extract priority items based on frequency/importance"""
        if not items_dict:
            return []
        
        # Sort by count/importance and return top items
        sorted_items = sorted(items_dict.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:10]]  # Top 10

    def _calculate_role_alignment(self, skills: Dict[str, int], software: Dict[str, int]) -> Dict[str, float]:
        """Calculate alignment with different roles based on skills"""
        
        role_keywords = {
            'Product Manager': ['product', 'strategy', 'roadmap', 'stakeholder'],
            'Product Analyst': ['analytics', 'metrics', 'kpi', 'dashboard'],
            'Business Analyst': ['business', 'requirements', 'process', 'workflow'],
            'Data Analyst': ['data', 'sql', 'python', 'tableau', 'analytics'],
            'Project Manager': ['project', 'gantt', 'timeline', 'management']
        }
        
        alignment_scores = {}
        all_items = list(skills.keys()) + list(software.keys())
        all_items_lower = [item.lower() for item in all_items]
        
        for role, keywords in role_keywords.items():
            score = 0
            for keyword in keywords:
                for item in all_items_lower:
                    if keyword in item:
                        score += 1
            
            alignment_scores[role] = score / len(keywords) if keywords else 0
        
        return alignment_scores

    def _extract_short_job_title(self, job_title_original: str) -> str:
        """Extract short job title for CV main title"""
        if not job_title_original:
            return ""
        
        # Remove common prefixes/suffixes
        title = job_title_original
        
        # Remove seniority levels
        title = re.sub(r'(?i)(senior|sr\.?|junior|jr\.?|lead|principal|chief)\s+', '', title)
        
        # Remove location info
        title = re.sub(r'\s*\([^)]*\)$', '', title)
        title = re.sub(r'\s*-\s*[^-]*$', '', title)
        
        # Clean up
        title = title.strip()
        
        return title

    def _calculate_data_completeness(self, basic_data: Dict[str, Any], 
                                   job_description: Dict[str, Any], 
                                   skills_summary: Dict[str, Any]) -> float:
        """Calculate overall data completeness score"""
        
        completeness_factors = []
        
        # Basic data completeness
        if basic_data.get('job_title_original'):
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        if basic_data.get('company'):
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        if basic_data.get('skills'):
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Job description completeness
        if job_description.get('source') == 'scrapped':
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Skills summary completeness
        if skills_summary.get('source') == 'csv_processed':
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        return sum(completeness_factors) / len(completeness_factors)

    def get_data_sources_status(self) -> Dict[str, Any]:
        """Get status of all data sources"""
        
        status = {
            'datapm_base': {
                'path': str(self.datapm_path),
                'exists': self.datapm_path.exists(),
                'accessible': False
            },
            'scrapped_folder': {
                'path': str(self.scrapped_path),
                'exists': self.scrapped_path.exists(),
                'file_count': 0,
                'accessible': False
            },
            'csv_processed_folder': {
                'path': str(self.csv_processed_path),
                'exists': self.csv_processed_path.exists(),
                'file_count': 0,
                'accessible': False
            }
        }
        
        # Check accessibility and count files
        try:
            if self.scrapped_path.exists():
                json_files = list(self.scrapped_path.glob("*.json"))
                status['scrapped_folder']['file_count'] = len(json_files)
                status['scrapped_folder']['accessible'] = True
        except Exception as e:
            status['scrapped_folder']['error'] = str(e)
        
        try:
            if self.csv_processed_path.exists():
                csv_files = list(self.csv_processed_path.glob("*.csv"))
                status['csv_processed_folder']['file_count'] = len(csv_files)
                status['csv_processed_folder']['accessible'] = True
        except Exception as e:
            status['csv_processed_folder']['error'] = str(e)
        
        try:
            status['datapm_base']['accessible'] = self.datapm_path.exists()
        except Exception as e:
            status['datapm_base']['error'] = str(e)
        
        return status

