"""
Manual CSV loader for PowerBI exports
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import glob

from ..utils.models import JobData
from ..utils.logger import LoggerMixin

class ManualLoader(LoggerMixin):
    """Load job data from manually exported CSV files"""
    
    def __init__(self, manual_exports_path: Path):
        super().__init__()
        self.manual_exports_path = manual_exports_path
        self.jobs_cache: Dict[str, JobData] = {}
        self._load_manual_jobs()
    
    def _load_manual_jobs(self):
        """Load all CSV files from manual exports directory"""
        if not self.manual_exports_path.exists():
            self.log_warning(f"Manual exports directory not found: {self.manual_exports_path}")
            return
        
        csv_files = list(self.manual_exports_path.glob("*.csv"))
        if not csv_files:
            self.log_info("No CSV files found in manual exports directory")
            return
        
        for csv_file in csv_files:
            try:
                self.log_info(f"Loading manual CSV: {csv_file.name}")
                # Try different encodings and separators
                try:
                    df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(csv_file, sep=';', encoding='latin-1')
                    except:
                        df = pd.read_csv(csv_file, sep=';', encoding='cp1252')
                
                for _, row in df.iterrows():
                    job_data = self._parse_job_row(row, csv_file.name)
                    if job_data:
                        self.jobs_cache[job_data.job_id] = job_data
                
                self.log_info(f"Loaded {len(df)} jobs from {csv_file.name}")
                
            except Exception as e:
                self.log_error(f"Error loading {csv_file.name}: {str(e)}")
    
    def _parse_job_row(self, row: pd.Series, source_file: str) -> Optional[JobData]:
        """Parse a single job row from CSV"""
        try:
            # Try to find job_id in various possible column names
            job_id = None
            for col in ['Job ID', 'job_id', 'id', 'jobid', 'ID', 'JobID']:
                if col in row.index and pd.notna(row[col]):
                    # Convert to string and remove .0 if it's a float
                    job_id = str(row[col]).replace('.0', '')
                    break
            
            if not job_id:
                # Generate a job_id if none found
                job_id = f"manual_{source_file}_{row.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract job data with fallbacks for different column names
            job_title = self._get_value(row, ['Job title (original)', 'job_title', 'title', 'position', 'role'])
            company = self._get_value(row, ['Company', 'company', 'company_name', 'employer'])
            skills = self._parse_list_field(row, ['Skills', 'skills', 'required_skills', 'key_skills'])
            software = self._parse_list_field(row, ['Software', 'software', 'tools', 'technologies'])
            seniority = self._get_value(row, ['Seniority', 'seniority', 'level', 'experience_level'])
            
            return JobData(
                job_id=job_id,
                job_title_original=job_title or "Unknown Position",
                job_title_short=job_title or "Unknown",
                company=company or "Unknown Company",
                skills=skills,
                software=software,
                seniority=seniority,
                experience_years="",
                job_schedule_type="",
                city="",
                state="",
                country="",
                degrees=[],
                source_file=source_file,
                raw_data=row.to_dict()
            )
            
        except Exception as e:
            self.log_error(f"Error parsing job row: {str(e)}")
            return None
    
    def _get_value(self, row: pd.Series, possible_columns: List[str]) -> str:
        """Get value from row using multiple possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                return str(row[col]).strip()
        return ""
    
    def _parse_list_field(self, row: pd.Series, possible_columns: List[str]) -> List[str]:
        """Parse a list field from CSV (skills, software, etc.)"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                value = str(row[col]).strip()
                if value:
                    # Split by common separators
                    items = [item.strip() for item in value.replace(';', ',').replace('|', ',').split(',') if item.strip()]
                    return items
        return []
    
    def load_job(self, job_id: str) -> Optional[JobData]:
        """Load a specific job by ID"""
        return self.jobs_cache.get(job_id)
    
    def get_all_jobs(self) -> List[JobData]:
        """Get all loaded jobs"""
        return list(self.jobs_cache.values())
    
    def search_jobs(self, query: str) -> List[JobData]:
        """Search jobs by title, company, or skills"""
        query_lower = query.lower()
        results = []
        
        for job in self.jobs_cache.values():
            if (query_lower in job.job_title_original.lower() or
                query_lower in job.company.lower() or
                any(query_lower in skill.lower() for skill in job.skills)):
                results.append(job)
        
        return results
    
    def get_job_count(self) -> int:
        """Get total number of loaded jobs"""
        return len(self.jobs_cache)
    
    def refresh_cache(self):
        """Reload all manual CSV files"""
        self.jobs_cache.clear()
        self._load_manual_jobs()
