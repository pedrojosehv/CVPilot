#!/usr/bin/env python3
"""
Simple test script for cover letter generation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.generation.cover_letter_generator import CoverLetterGenerator
from src.utils.config import Config
from src.ingest.manual_loader import ManualLoader
from src.matching.profile_matcher import ProfileMatcher
from src.generation.content_generator import ContentGenerator
from src.validation.content_validator import ContentValidator

def test_cover_letter():
    """Test cover letter generation"""
    
    # Initialize components
    config = Config()
    loader = ManualLoader(config.manual_exports_path)
    matcher = ProfileMatcher(config.profiles_path)
    generator = ContentGenerator(config.llm_config, str(config.datapm_path))
    validator = ContentValidator()
    
    # Load job data
    job_data = loader.load_job('10')
    print(f"Loaded job: {job_data.job_title_original} at {job_data.company}")
    
    # Match profile
    match_result = matcher.match_job_to_profile(job_data, "product_management")
    print(f"Initial fit score: {match_result.fit_score:.3f}")
    
    # Generate content
    replacements = generator.generate_replacements(job_data, match_result)
    print("Content generated successfully")
    
    # Validate content
    validation_result = validator.validate_replacements(replacements)
    if validation_result.is_valid:
        print("Content validated successfully")
    else:
        print("Validation errors:", validation_result.errors)
        return
    
    # Test cover letter generation
    cover_letter_gen = CoverLetterGenerator(config.llm_config, str(config.datapm_path))
    
    # Extract CV content for cover letter generation (ensure all are strings)
    cv_content = {
        'profile_summary': str(replacements.profile_summary.content),
        'skill_list': ', '.join(replacements.skill_list.content) if isinstance(replacements.skill_list.content, list) else str(replacements.skill_list.content),
        'software_list': ', '.join(replacements.software_list.content) if isinstance(replacements.software_list.content, list) else str(replacements.software_list.content)
    }
    
    print("CV content prepared:")
    print(f"  Profile summary: {cv_content['profile_summary'][:100]}...")
    print(f"  Skills: {cv_content['skill_list'][:100]}...")
    print(f"  Software: {cv_content['software_list'][:100]}...")
    
    # Generate cover letter
    try:
        cover_letter_content = cover_letter_gen.generate_cover_letter(job_data, match_result, cv_content)
        print(f"\nCover letter generated successfully ({len(cover_letter_content)} characters)")
        print("\n" + "="*50)
        print("COVER LETTER:")
        print("="*50)
        print(cover_letter_content)
        print("="*50)
        
        # Save to file
        output_file = Path("test_cover_letter.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
        print(f"\nCover letter saved to: {output_file}")
        
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cover_letter()
