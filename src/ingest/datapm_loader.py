"""
DataPM CSV loader for retrieving original job descriptions
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import glob

from ..utils.logger import LoggerMixin

class DataPMLoader(LoggerMixin):
    """Load job descriptions from DataPM CSV files"""
    
    def __init__(self, datapm_path: Path):
        super().__init__()
        self.datapm_path = datapm_path
        self.scrapped_path = datapm_path / "csv" / "src" / "scrapped"
        self.processed_path = datapm_path / "csv" / "src" / "csv_processed"
    
    def find_job_description(self, job_title: str, company: str) -> Optional[Dict[str, Any]]:
        """Find job description by matching job title and company"""
        
        self.log_info(f"🔍 Searching for job description: '{job_title}' at '{company}'")
        
        # First try processed files (more structured)
        job_data = self._search_in_processed_files(job_title, company)
        if job_data:
            return job_data
        
        # If not found, try scrapped files (raw data)
        job_data = self._search_in_scrapped_files(job_title, company)
        if job_data:
            return job_data
        
        self.log_warning(f"⚠️ Job description not found for '{job_title}' at '{company}'")
        return None
    
    def _search_in_processed_files(self, job_title: str, company: str) -> Optional[Dict[str, Any]]:
        """Search in processed CSV files"""
        
        if not self.processed_path.exists():
            self.log_warning(f"⚠️ Processed path does not exist: {self.processed_path}")
            return None
        
        # Find all CSV files in processed directory
        csv_files = glob.glob(str(self.processed_path / "*.csv"))
        
        for csv_file in csv_files:
            try:
                self.log_info(f"🔍 Searching in processed file: {Path(csv_file).name}")
                df = pd.read_csv(csv_file)
                
                # Look for matching job title and company
                # Try different possible column names
                title_columns = ['job_title', 'Job Title', 'title', 'position', 'role']
                company_columns = ['company', 'Company', 'company_name', 'employer']
                
                title_col = None
                company_col = None
                
                for col in title_columns:
                    if col in df.columns:
                        title_col = col
                        break
                
                for col in company_columns:
                    if col in df.columns:
                        company_col = col
                        break
                
                if title_col and company_col:
                    # Normalize for comparison
                    df['title_normalized'] = df[title_col].astype(str).str.lower().str.strip()
                    df['company_normalized'] = df[company_col].astype(str).str.lower().str.strip()
                    
                    target_title = job_title.lower().strip()
                    target_company = company.lower().strip()
                    
                    # Find matches
                    matches = df[
                        (df['title_normalized'] == target_title) & 
                        (df['company_normalized'] == target_company)
                    ]
                    
                    if not matches.empty:
                        match = matches.iloc[0]
                        self.log_info(f"✅ Found match in processed file: {Path(csv_file).name}")
                        
                        # Extract job description if available
                        description = None
                        desc_columns = ['description', 'Description', 'job_description', 'details']
                        for col in desc_columns:
                            if col in df.columns and pd.notna(match[col]):
                                description = str(match[col])
                                break
                        
                        return {
                            'job_title': str(match[title_col]),
                            'company': str(match[company_col]),
                            'description': description,
                            'source_file': Path(csv_file).name,
                            'source_type': 'processed'
                        }
                
            except Exception as e:
                self.log_error(f"Error reading processed file {csv_file}: {str(e)}")
                continue
        
        return None
    
    def _search_in_scrapped_files(self, job_title: str, company: str) -> Optional[Dict[str, Any]]:
        """Search in scrapped CSV files (raw data)"""
        
        if not self.scrapped_path.exists():
            self.log_warning(f"⚠️ Scrapped path does not exist: {self.scrapped_path}")
            return None
        
        # Find all CSV files in scrapped directory
        csv_files = glob.glob(str(self.scrapped_path / "*.csv"))
        
        for csv_file in csv_files:
            try:
                self.log_info(f"🔍 Searching in scrapped file: {Path(csv_file).name}")
                df = pd.read_csv(csv_file)
                
                # Look for matching job title and company
                # Try different possible column names
                title_columns = ['job_title', 'Job Title', 'title', 'position', 'role', 'job_title_original']
                company_columns = ['company', 'Company', 'company_name', 'employer']
                
                title_col = None
                company_col = None
                
                for col in title_columns:
                    if col in df.columns:
                        title_col = col
                        break
                
                for col in company_columns:
                    if col in df.columns:
                        company_col = col
                        break
                
                if title_col and company_col:
                    # Normalize for comparison
                    df['title_normalized'] = df[title_col].astype(str).str.lower().str.strip()
                    df['company_normalized'] = df[company_col].astype(str).str.lower().str.strip()
                    
                    target_title = job_title.lower().strip()
                    target_company = company.lower().strip()
                    
                    # Find matches
                    matches = df[
                        (df['title_normalized'] == target_title) & 
                        (df['company_normalized'] == target_company)
                    ]
                    
                    if not matches.empty:
                        match = matches.iloc[0]
                        self.log_info(f"✅ Found match in scrapped file: {Path(csv_file).name}")
                        
                        # Extract job description if available
                        description = None
                        desc_columns = ['description', 'Description', 'job_description', 'details', 'job_description_original']
                        for col in desc_columns:
                            if col in df.columns and pd.notna(match[col]):
                                description = str(match[col])
                                break
                        
                        return {
                            'job_title': str(match[title_col]),
                            'company': str(match[company_col]),
                            'description': description,
                            'source_file': Path(csv_file).name,
                            'source_type': 'scrapped'
                        }
                
            except Exception as e:
                self.log_error(f"Error reading scrapped file {csv_file}: {str(e)}")
                continue
        
        return None
