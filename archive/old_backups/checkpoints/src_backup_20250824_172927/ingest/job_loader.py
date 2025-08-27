"""
Job data loader from DataPM CSV files
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from ..utils.models import JobData
from ..utils.logger import LoggerMixin

class JobLoader(LoggerMixin):
    """Load job data from DataPM CSV files"""
    
    def __init__(self, data_path: Path):
        super().__init__()
        self.data_path = data_path
        self.jobs_cache: Dict[str, JobData] = {}
        self._load_all_jobs()
    
    def _load_all_jobs(self):
        """Load all jobs from CSV files into cache"""
        csv_files = list(self.data_path.glob("*.csv"))
        
        if not csv_files:
            self.log_warning(f"No CSV files found in {self.data_path}")
            return
        
        all_jobs = []
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                self.log_info(f"Loaded {len(df)} jobs from {csv_file.name}")
                
                # Add source file info
                df['source_file'] = csv_file.name
                all_jobs.append(df)
                
            except Exception as e:
                self.log_error(f"Error loading {csv_file}: {str(e)}")
        
        if all_jobs:
            # Combine all dataframes
            combined_df = pd.concat(all_jobs, ignore_index=True)
            
            # Create job ID if not exists (using index for now)
            if 'job_id' not in combined_df.columns:
                combined_df['job_id'] = combined_df.index.astype(str)
            
            # Convert to JobData objects
            for _, row in combined_df.iterrows():
                try:
                    job_data = self._row_to_job_data(row)
                    self.jobs_cache[job_data.job_id] = job_data
                except Exception as e:
                    self.log_error(f"Error converting row to JobData: {str(e)}")
            
            self.log_info(f"Loaded {len(self.jobs_cache)} jobs into cache")
    
    def _row_to_job_data(self, row: pd.Series) -> JobData:
        """Convert pandas row to JobData object"""
        
        # Map CSV columns to JobData fields
        job_data = JobData(
            job_id=str(row.get('job_id', row.name)),
            job_title_original=str(row.get('Job title (original)', '')),
            job_title_short=str(row.get('Job title (short)', '')),
            company=str(row.get('Company', '')),
            country=str(row.get('Country', '')),
            state=row.get('State') if pd.notna(row.get('State')) else None,
            city=row.get('City') if pd.notna(row.get('City')) else None,
            schedule_type=row.get('Schedule type') if pd.notna(row.get('Schedule type')) else None,
            experience_years=row.get('Experience years') if pd.notna(row.get('Experience years')) else None,
            seniority=row.get('Seniority') if pd.notna(row.get('Seniority')) else None,
            skills=row.get('Skills', ''),
            degrees=row.get('Degrees', ''),
            software=row.get('Software', '')
        )
        
        return job_data
    
    def load_job(self, job_id: str) -> Optional[JobData]:
        """Load specific job by ID"""
        if job_id in self.jobs_cache:
            return self.jobs_cache[job_id]
        
        self.log_warning(f"Job ID {job_id} not found in cache")
        return None
    
    def search_jobs(self, 
                   company: Optional[str] = None,
                   job_title: Optional[str] = None,
                   skills: Optional[List[str]] = None,
                   limit: int = 10) -> List[JobData]:
        """Search jobs by criteria"""
        
        results = []
        
        for job in self.jobs_cache.values():
            match = True
            
            if company and company.lower() not in job.company.lower():
                match = False
            
            if job_title and job_title.lower() not in job.job_title_original.lower():
                match = False
            
            if skills:
                job_skills_lower = [skill.lower() for skill in job.skills]
                for skill in skills:
                    if skill.lower() not in job_skills_lower:
                        match = False
                        break
            
            if match:
                results.append(job)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded jobs"""
        if not self.jobs_cache:
            return {}
        
        companies = [job.company for job in self.jobs_cache.values()]
        skills = []
        software = []
        
        for job in self.jobs_cache.values():
            skills.extend(job.skills)
            software.extend(job.software)
        
        return {
            'total_jobs': len(self.jobs_cache),
            'unique_companies': len(set(companies)),
            'unique_skills': len(set(skills)),
            'unique_software': len(set(software)),
            'top_companies': pd.Series(companies).value_counts().head(5).to_dict(),
            'top_skills': pd.Series(skills).value_counts().head(10).to_dict(),
            'top_software': pd.Series(software).value_counts().head(10).to_dict()
        }
    
    def refresh_cache(self):
        """Refresh job cache from CSV files"""
        self.jobs_cache.clear()
        self._load_all_jobs()
        self.log_info("Job cache refreshed")
