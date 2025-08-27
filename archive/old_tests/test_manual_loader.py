#!/usr/bin/env python3
"""
Test script for manual loader functionality
"""

import sys
from pathlib import Path
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ingest.manual_loader import ManualLoader
from src.utils.config import Config

def create_sample_csv():
    """Create a sample CSV file for testing"""
    sample_data = {
        'job_id': ['JOB001', 'JOB002', 'JOB003'],
        'job_title': ['Product Manager', 'Senior Product Manager', 'Product Owner'],
        'company': ['TechCorp', 'StartupXYZ', 'Enterprise Inc'],
        'skills': ['Product Strategy, Agile, User Research', 'Product Management, Analytics, Leadership', 'Scrum, Stakeholder Management, Roadmapping'],
        'software': ['Jira, Figma, Analytics', 'Productboard, Mixpanel, Slack', 'Azure DevOps, Miro, Confluence'],
        'seniority': ['Mid', 'Senior', 'Mid']
    }
    
    df = pd.DataFrame(sample_data)
    csv_path = Path("manual_exports/sample_jobs.csv")
    csv_path.parent.mkdir(exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"Created sample CSV: {csv_path}")
    return csv_path

def test_manual_loader():
    """Test the manual loader functionality"""
    print("🧪 Testing Manual Loader...")
    
    # Create sample CSV
    csv_path = create_sample_csv()
    
    # Initialize config and loader
    config = Config()
    loader = ManualLoader(config.manual_exports_path)
    
    print(f"📊 Loaded {loader.get_job_count()} jobs")
    
    # Test loading specific job
    job = loader.load_job("JOB001")
    if job:
        print(f"✅ Found job: {job.job_title_original} at {job.company}")
        print(f"   Skills: {job.skills[:3]}...")
        print(f"   Software: {job.software[:3]}...")
    else:
        print("❌ Job JOB001 not found")
    
    # Test search functionality
    search_results = loader.search_jobs("Product")
    print(f"🔍 Found {len(search_results)} jobs matching 'Product'")
    
    # List all jobs
    all_jobs = loader.get_all_jobs()
    print(f"📋 All jobs:")
    for job in all_jobs:
        print(f"   - {job.job_id}: {job.job_title_original} at {job.company}")
    
    # Clean up
    csv_path.unlink()
    print("🧹 Cleaned up sample CSV")

if __name__ == "__main__":
    test_manual_loader()

