#!/usr/bin/env python3
"""
CVPilot - Main Entry Point
CV Automation Tool for job-specific customization
"""

import click
import logging
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

from .ingest.job_loader import JobLoader
from .ingest.manual_loader import ManualLoader
from .matching.profile_matcher import ProfileMatcher
from .generation.content_generator import ContentGenerator
from .generation.cover_letter_generator import CoverLetterGenerator
from .validation.content_validator import ContentValidator
from .template.docx_processor import DocxProcessor
from .utils.config import Config
from .utils.logger import setup_logger
from .utils.models import Replacements, ReplacementBlock
from .utils.naming_utils import NamingUtils
from .utils.template_selector import TemplateSelector
from .utils.user_profile_manager import UserProfileManager
from .utils.auto_llm_selector import AutoLLMSelector

def _save_text_without_overwrite(file_path: Path, content: str) -> Path:
    """CRITICAL SAFETY RULE: NEVER OVERWRITE EXISTING TEXT FILES

    This function implements the mandatory no-overwrite policy for text files:
    - If file exists: Generate unique filename with timestamp
    - If file doesn't exist: Save with original filename
    - Always preserves existing files to prevent data loss
    """
    import datetime

    if file_path.exists():
        # File exists - generate unique filename to avoid overwrite
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = file_path.stem
        suffix = file_path.suffix
        unique_filename = f"{stem}_{timestamp}{suffix}"
        unique_file = file_path.parent / unique_filename

        with open(unique_file, 'w', encoding='utf-8') as f:
            f.write(content)

        console.print(f"[yellow]⚠️ FILE EXISTS - Cover letter saved as: {unique_filename}[/yellow]")
        console.print(f"[yellow]   Original file preserved: {file_path.name}[/yellow]")

        return unique_file
    else:
        # File doesn't exist - save normally
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

def _determine_job_category(job_data, match_result):
    """Determine job category for file organization"""
    
    # Extract key information
    job_title = job_data.job_title_original.lower() if job_data.job_title_original else ""
    skills = [skill.lower() for skill in job_data.skills] if job_data.skills else []
    software = [tool.lower() for tool in job_data.software] if job_data.software else []
    
    # Define category keywords
    categories = {
        'product_management': ['product', 'pm', 'product manager', 'product owner', 'scrum'],
        'data_analytics': ['data', 'analytics', 'analyst', 'bi', 'business intelligence', 'sql', 'tableau', 'power bi'],
        'marketing': ['marketing', 'growth', 'digital marketing', 'seo', 'sem', 'social media'],
        'sales': ['sales', 'business development', 'account', 'customer success'],
        'engineering': ['engineer', 'developer', 'programming', 'software', 'technical', 'python', 'java', 'javascript'],
        'design': ['design', 'ux', 'ui', 'user experience', 'creative', 'visual'],
        'operations': ['operations', 'project', 'process', 'strategy', 'business'],
        'finance': ['finance', 'financial', 'accounting', 'budget', 'investment']
    }
    
    # Calculate category scores
    category_scores = {}
    for category, keywords in categories.items():
        score = 0
        # Check job title
        for keyword in keywords:
            if keyword in job_title:
                score += 3  # Higher weight for title matches
        
        # Check skills
        for skill in skills:
            for keyword in keywords:
                if keyword in skill:
                    score += 1
        
        # Check software
        for tool in software:
            for keyword in keywords:
                if keyword in tool:
                    score += 1
        
        category_scores[category] = score
    
    # Find best category
    best_category = max(category_scores.items(), key=lambda x: x[1])
    
    # If no clear category, use fit score to determine
    if best_category[1] == 0:
        if match_result.fit_score > 0.5:
            return 'high_match'
        elif match_result.fit_score > 0.3:
            return 'medium_match'
        else:
            return 'low_match'
    
    return best_category[0]

console = Console()

@click.command()
@click.option('--job-id', required=True, help='Job ID to process')
@click.option('--profile-type', default='product_management', help='Profile type to use')
@click.option('--template-path', help='Path to CV template (auto-selected if not provided)')
@click.option('--auto-template', is_flag=True, help='Automatically select best template from existing CVs')
@click.option('--output-dir', default='./output', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Run in dry-run mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--cv-only', is_flag=True, help='Generate only CV')
@click.option('--cover-letter-only', is_flag=True, help='Generate only cover letter')
@click.option('--both', is_flag=True, default=True, help='Generate both CV and cover letter (default)')
@click.option('--sequential', is_flag=True, default=True, help='Generate CV and cover letter sequentially (default)')
@click.option('--auto-select-llm', is_flag=True, help='Automatically select the best available LLM')
def main(job_id, profile_type, template_path, auto_template, output_dir, dry_run, verbose, cv_only, cover_letter_only, both, sequential, auto_select_llm=False):
    """
    CVPilot - Generate customized CV based on job description
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger(log_level)
    
    # Load configuration
    config = Config()

    # Auto-select best LLM if requested or if current model seems suboptimal
    if auto_select_llm or _should_auto_select_llm(config):
        console.print("[blue]🤖 Running automatic LLM selection...[/blue]")
        try:
            selector = AutoLLMSelector(job_id, verbose)
            selection_result = selector.auto_select_best_llm()
            console.print(f"[green]✅ Auto-selected: {selection_result.best_provider.upper()} - {selection_result.best_model}[/green]")

            # Reload config with new selection
            config = Config()
        except Exception as e:
            console.print(f"[yellow]⚠️ Auto-selection failed: {e}[/yellow]")
            console.print("[yellow]Continuing with current configuration...[/yellow]")

    # Initialize User Profile Manager - ALWAYS LOAD AND REFRESH USER DATA
    console.print("[blue]👤 Initializing user profile system...[/blue]")
    profile_manager = UserProfileManager()

    # ALWAYS extract fresh user information from templates (MANDATORY)
    console.print("[blue]🔄 Refreshing user profile data from templates...[/blue]")
    if config.templates_path.exists():
        templates_found = 0
        for template_file in config.templates_path.glob("*.docx"):
            console.print(f"[blue]📊 Extracting profile data from: {template_file.name}[/blue]")
            profile_manager.extract_from_cv_template(str(template_file))
            templates_found += 1

        if templates_found == 0:
            console.print("[yellow]⚠️ No CV templates found for profile extraction[/yellow]")
        else:
            console.print(f"[green]✅ Profile extracted from {templates_found} template(s)[/green]")
    else:
        console.print("[red]❌ Templates directory not found[/red]")

    # Display profile summary for verification
    profile_summary = profile_manager.get_profile_summary()
    console.print(f"[cyan]📈 Profile Status: {profile_summary['experience_years']} years exp, {len(profile_summary['top_skills'])} skills, {len(profile_summary['recent_experience'])} recent roles[/cyan]")

    # Save profile to ensure persistence
    profile_manager.save_profile()
    console.print("[green]💾 User profile saved and ready[/green]")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    console.print(f"[bold blue]CVPilot[/bold blue] - Processing job ID: {job_id}")
    console.print(f"Profile type: {profile_type}")
    console.print(f"Dry run: {dry_run}")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            # Step 1: Ingest job data - ONLY FROM MANUAL_EXPORT.CSV
            task1 = progress.add_task("Loading job data from manual_export.csv...", total=None)

            # ONLY search in manual_export.csv as specified by user
            manual_loader = ManualLoader(config.manual_exports_path)
            job_data = manual_loader.load_job(job_id)

            # NO DataPM loader - only manual_export.csv as per user instructions
            if not job_data:
                console.print(f"[red]Error: Job ID {job_id} not found in manual_export.csv[/red]")
                console.print(f"[yellow]Available jobs in manual_export.csv: {manual_loader.get_job_count()}[/yellow]")
                return 1

            progress.update(task1, completed=True)

            # Step 2: Analyze existing outputs and select best template
            task2 = progress.add_task("Analyzing existing outputs and selecting best template...", total=None)

            # Always analyze existing outputs to select best template
            console.print("[blue]🔍 Analyzing existing CV outputs for intelligent template selection...[/blue]")
            template_selector = TemplateSelector(output_dir)
            best_template = template_selector.find_best_template(job_data, profile_type)

            if best_template:
                selected_template_path = str(best_template.file_path)
                console.print(f"[green]✅ Best template selected: {best_template.file_path.name}[/green]")
                console.print(f"[green]   Match Score: {best_template.score:.2f} | Reasons: {', '.join(best_template.match_reasons)}[/green]")
            else:
                console.print("[yellow]⚠️ No existing outputs found, using default template[/yellow]")
                selected_template_path = config.default_template_path

            # Use selected template (from analysis or default)
            if template_path:
                selected_template_path = template_path
                console.print(f"[blue]Using specified template: {template_path}[/blue]")

            progress.update(task2, completed=True)

            # Step 3: Calculate fit score compared to selected template
            task3 = progress.add_task("Calculating fit score compared to selected template...", total=None)
            matcher = ProfileMatcher(config.profiles_path)
            match_result = matcher.match_job_to_profile(job_data, profile_type)
            console.print(f"[green]📊 Fit Score: {match_result.fit_score:.3f} (compared to selected template)[/green]")
            progress.update(task3, completed=True)

            # Step 4: Generate content
            task4 = progress.add_task("Generating content...", total=None)
            generator = ContentGenerator(
                config.llm_config,
                str(config.datapm_path),
                str(config.templates_path),
                user_profile_manager=profile_manager
            )
            
            # Determine what to generate based on flags FIRST
            # If specific flags are used, disable 'both' default behavior
            if cv_only or cover_letter_only:
                both = False

            generate_cv = cv_only or both
            generate_cover_letter = cover_letter_only or both

            # Only generate CV content if we need to generate a CV
            if generate_cv:
                # Use multi-template processor by default
                if hasattr(generator, 'multi_template_processor') and generator.multi_template_processor:
                    console.print("[green]✅ Using multi-template processing (pool of CVs)...[/green]")
                    replacements = generator.generate_optimized_replacements(job_data, match_result, selected_template_path or config.default_template_path)
                else:
                    console.print("[yellow]⚠️ Multi-template processor not available, falling back to standard generation...[/yellow]")
                    replacements = generator.generate_replacements(job_data, match_result)

                progress.update(task4, completed=True)

                # Step 5: Validate content
                task5 = progress.add_task("Validating content...", total=None)
                validator = ContentValidator()
                validation_result = validator.validate_replacements(replacements)
                progress.update(task5, completed=True)

                if not validation_result.is_valid:
                    console.print(f"[red]Validation failed: {validation_result.errors}[/red]")
                    return 1
            else:
                # Skip CV content generation and validation
                console.print("[blue]📝 Skipping CV content generation (--cover-letter-only mode)[/blue]")
                # Create minimal replacements object for cover letter generation
                replacements = Replacements(
                    profile_summary=ReplacementBlock(placeholder="ProfileSummary", content="", confidence=1.0),
                    skill_list=ReplacementBlock(placeholder="SkillList", content="", confidence=1.0),
                    software_list=ReplacementBlock(placeholder="SoftwareList", content="", confidence=1.0),
                    objective_title=ReplacementBlock(placeholder="ObjectiveTitle", content="", confidence=1.0),
                    ats_recommendations=ReplacementBlock(placeholder="ATSRecommendations", content="", confidence=1.0),
                    job_id=job_data.job_id,
                    company=job_data.company,
                    position=job_data.job_title_original,
                    generated_at=datetime.now().isoformat(),
                    top_bullets=[
                        ReplacementBlock(placeholder="TopBullet1", content="", confidence=1.0),
                        ReplacementBlock(placeholder="TopBullet2", content="", confidence=1.0),
                        ReplacementBlock(placeholder="TopBullet3", content="", confidence=1.0)
                    ]
                )
                progress.update(task4, completed=True)
                # task5 is not created in cover-letter-only mode, so no need to update it
            
            # Configure sequential execution by default
            if sequential and generate_cv and generate_cover_letter:
                console.print("[blue]🔄 Sequential execution enabled: CV first, then Cover Letter[/blue]")
            
            output_files = []
            
            # Step 6: Generate CV if requested
            if generate_cv:
                task6 = progress.add_task("Processing CV template...", total=None)
                processor = DocxProcessor()
                
                # Use selected template (already handled by auto-selection logic)
                if not selected_template_path:
                    selected_template_path = config.default_template_path

                # Determine job category for organization
                job_category = _determine_job_category(job_data, match_result)

                # Process template
                if dry_run:
                    output_file = processor.generate_dry_run(selected_template_path, replacements, output_path)
                    console.print(f"[yellow]CV dry run completed. Output: {output_file}[/yellow]")
                else:
                    output_file = processor.process_template(selected_template_path, replacements, output_path, job_category)
                    console.print(f"[green]CV generated successfully: {output_file}[/green]")
                    console.print(f"[blue]Category: {job_category}[/blue]")
                
                output_files.append(output_file)
                progress.update(task5, completed=True)
            
            # Step 5b: Generate Cover Letter if requested
            if generate_cover_letter:
                task5b = progress.add_task("Generating cover letter...", total=None)
                
                # Initialize cover letter generator
                cover_letter_gen = CoverLetterGenerator(config.llm_config, str(config.datapm_path))
                
                # Extract CV content for cover letter generation (ensure all are strings)
                cv_content = {
                    'profile_summary': str(replacements.profile_summary.content),
                    'skill_list': ', '.join(replacements.skill_list.content) if isinstance(replacements.skill_list.content, list) else str(replacements.skill_list.content),
                    'software_list': ', '.join(replacements.software_list.content) if isinstance(replacements.software_list.content, list) else str(replacements.software_list.content)
                }
                
                # Generate cover letter
                cover_letter_content = cover_letter_gen.generate_cover_letter(job_data, match_result, cv_content)
                
                # Generate cover letter filename first
                cover_letter_filename = NamingUtils.generate_filename(
                    job_data.job_title_original,
                    job_data.software,
                    job_data.company,
                    "cover_letter"
                )

                # Determine output path for cover letter
                if generate_cv and not dry_run:
                    # Use the same folder as CV
                    cv_folder = output_files[0].parent
                else:
                    # Find the most recent folder with a CV that has the same base filename
                    cv_folder = NamingUtils.find_most_recent_cv_folder(output_path, cover_letter_filename)
                    if cv_folder == output_path:
                        # If no existing CV folder found, create a new category-based folder
                        job_category = _determine_job_category(job_data, match_result)
                        cv_folder = output_path / job_category
                        cv_folder.mkdir(exist_ok=True)
                cover_letter_file = cv_folder / cover_letter_filename
                
                # Save cover letter - NO OVERWRITE RULE
                cover_letter_file = _save_text_without_overwrite(cover_letter_file, cover_letter_content)
                
                console.print(f"[green]Cover letter generated successfully: {cover_letter_file}[/green]")
                output_files.append(cover_letter_file)
                progress.update(task5b, completed=True)
            
            # Step 6: Calculate final fit score comparison (only if CV was generated)
            if generate_cv:
                task6 = progress.add_task("Calculating fit score improvement...", total=None)
                final_fit_analysis = matcher.calculate_final_fit_score(job_data, profile_type, replacements)
                progress.update(task6, completed=True)
            else:
                # For cover letter only, use initial match result
                final_fit_analysis = {
                    'initial_fit_score': match_result.fit_score,
                    'final_fit_score': match_result.fit_score,
                    'improvement': 0.0
                }
            
            # Record successful summary for learning system
            if generate_cv and final_fit_analysis['improvement'] >= 0.05:  # Only record significantly successful summaries
                try:
                    from .utils.template_learning_system import TemplateLearningSystem
                    learning_system = TemplateLearningSystem()

                    summary_text = replacements.profile_summary.content
                    fit_improvement = final_fit_analysis['improvement']

                    learning_system.record_successful_summary(
                        summary_text=summary_text,
                        job_data=job_data,
                        fit_score_improvement=fit_improvement
                    )

                    logger.info(f"💡 Recorded successful summary for learning (improvement: {fit_improvement:.3f})")
                except Exception as e:
                    logger.warning(f"Failed to record successful summary: {e}")

            # Learn from this interaction to improve future generations
            console.print("[blue]🧠 Learning from this interaction...[/blue]")
            try:
                # Create a processing result object for learning
                from .utils.models import ProcessingResult
                processing_result = ProcessingResult(
                    job_id=job_id,
                    output_file=str(output_files[0]) if output_files else "",
                    fit_score=final_fit_analysis['final_fit_score'],
                    processing_time=0.0,  # Could be tracked better in future
                    replacements=replacements,
                    validation_result=None,  # Could be added later
                    success=True
                )

                # Learn from this interaction
                profile_manager.learn_from_interaction(job_data, processing_result)

                # Get personalized suggestions for next time
                suggestions = profile_manager.get_personalized_content_suggestions(job_data)
                if suggestions['skill_match_score'] > 0.5:
                    console.print(f"[green]💡 Profile learning: High skill match ({suggestions['skill_match_score']:.1%})[/green]")
                else:
                    console.print(f"[yellow]💡 Profile learning: Consider adding {len(job_data.skills) - len(suggestions.get('recommended_skills', []))} more skills[/yellow]")

                logger.info("🧠 Successfully learned from interaction and updated user profile")

            except Exception as e:
                logger.warning(f"Failed to learn from interaction: {e}")

            # Log results
            logger.info(f"Job {job_id} processed successfully")
            logger.info(f"Initial fit score: {match_result.fit_score:.3f}")
            logger.info(f"Final fit score: {final_fit_analysis['final_fit_score']:.3f}")
            logger.info(f"Improvement: {final_fit_analysis['improvement']:.3f}")
            for output_file in output_files:
                logger.info(f"Output file: {output_file}")
            
            # Extract naming information for display
            role_initials = NamingUtils.extract_role_initials(job_data.job_title_original)
            software_category = NamingUtils.extract_software_category(job_data.software)
            business_model = NamingUtils.extract_business_model(job_data.job_title_original, job_data.company)
            folder_name = NamingUtils.generate_folder_name(job_data.job_title_original, job_data.software)
        
        # Display summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Job ID: {job_id}")
        console.print(f"  Company: {job_data.company}")
        console.print(f"  Position: {job_data.job_title_original}")
        console.print(f"  Initial Fit Score: {match_result.fit_score:.3f}")
        console.print(f"  Final Fit Score: {final_fit_analysis['final_fit_score']:.3f}")
        console.print(f"  Improvement: {final_fit_analysis['improvement']:.3f}")
        for output_file in output_files:
            console.print(f"  Output: {output_file}")
        
        # Display naming information
        console.print("\n[bold]File Organization:[/bold]")
        if generate_cv:
            console.print(f"  CV Filename: PedroHerrera_{role_initials}_{software_category}_{business_model}_2025.docx")
        if generate_cover_letter:
            console.print(f"  Cover Letter Filename: PedroHerrera_{role_initials}_{software_category}_{business_model}_2025_CoverLetter.txt")
        console.print(f"  Folder: {folder_name}")
        console.print(f"  Role Initials: {role_initials}")
        console.print(f"  Software Category: {software_category}")
        console.print(f"  Business Model: {business_model}")
        
        # Display detailed improvement analysis
        console.print("\n[bold]Fit Score Analysis:[/bold]")
        if 'skill_improvement' in final_fit_analysis:
            console.print(f"  Skills Improvement: {final_fit_analysis['skill_improvement']:+d} skills")
        if 'software_improvement' in final_fit_analysis:
            console.print(f"  Software Improvement: {final_fit_analysis['software_improvement']:+d} tools")
        if final_fit_analysis.get('new_skills_added'):
            console.print(f"  New Skills Added: {', '.join(final_fit_analysis['new_skills_added'][:5])}")
        if final_fit_analysis.get('new_software_added'):
            console.print(f"  New Software Added: {', '.join(final_fit_analysis['new_software_added'][:3])}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def _should_auto_select_llm(config) -> bool:
    """
    Determine if automatic LLM selection should be triggered

    Returns True if:
    - No LLM provider is configured
    - Current model is not a modern model (like gpt-4o, claude-3-5-sonnet, etc.)
    - Environment suggests this is first run
    """

    # Check if no provider is configured
    if not os.getenv("LLM_PROVIDER"):
        return True

    # Check if current model is outdated
    current_model = os.getenv("LLM_MODEL", "").lower()
    outdated_models = [
        "gpt-4", "gpt-3.5", "claude-3", "claude-2", "gemini-pro", "gemini-1.5",
        "text-davinci", "text-curie", "text-babbage", "text-ada"
    ]

    if any(outdated in current_model for outdated in outdated_models):
        return True

    # Check if this looks like a default/basic configuration
    if current_model in ["gpt-4", "claude-3-haiku", "gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]:
        return True

    return False

if __name__ == "__main__":
    main()
