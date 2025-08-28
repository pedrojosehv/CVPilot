#!/usr/bin/env python3
"""
CVPilot Enhanced - Main Entry Point with New Workflow
CV Automation Tool with database-driven profile selection and complete DataPM integration
"""

import click
import logging
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from datetime import datetime

# Core imports
from .ingest.job_loader import JobLoader
from .generation.content_generator import ContentGenerator
from .generation.cover_letter_generator import CoverLetterGenerator
from .validation.content_validator import ContentValidator
from .template.docx_processor import DocxProcessor
from .utils.config import Config
from .utils.logger import setup_logger
from .utils.models import Replacements, ReplacementBlock, JobData
from .utils.naming_utils import NamingUtils

# Enhanced imports
from .utils.cv_monitor import CVMonitor
from .utils.role_content_manager import RoleContentManager
from .utils.database_profile_selector import DatabaseProfileSelector
from .utils.datapm_enhanced_loader import EnhancedDataPMLoader
from .utils.user_profile_manager import UserProfileManager
from .utils.auto_llm_selector import AutoLLMSelector

console = Console()

def _save_text_without_overwrite(file_path: Path, content: str) -> Path:
    """CRITICAL SAFETY RULE: NEVER OVERWRITE EXISTING TEXT FILES"""
    import datetime
    if file_path.exists():
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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path

@click.command()
@click.option('--job-id', required=True, help='Job ID to process')
@click.option('--profile-type', default='auto', help='Profile type (auto for database selection)')
@click.option('--output-dir', default='./output', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Run in dry-run mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--cv-only', is_flag=True, help='Generate only CV')
@click.option('--cover-letter-only', is_flag=True, help='Generate only cover letter')
@click.option('--both', is_flag=True, default=True, help='Generate both CV and cover letter (default)')
@click.option('--force-sync', is_flag=True, help='Force full database synchronization')
@click.option('--auto-select-llm', is_flag=True, help='Automatically select the best available LLM')
def main(job_id, profile_type, output_dir, dry_run, verbose, cv_only, cover_letter_only, both, force_sync, auto_select_llm=False):
    """
    CVPilot Enhanced - Generate customized CV with database-driven workflow
    
    New workflow:
    1. Check for CV changes and sync database
    2. Load complete job data from DataPM (scrapped + csv_processed)
    3. Select best profile from role database
    4. Generate content using selected profile + job context
    """
    
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger(log_level)
    
    console.print("\n[bold blue]🚀 CVPilot Enhanced - Database-Driven CV Generation[/bold blue]\n")
    
    # Load configuration
    config = Config()
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Auto-select best LLM if requested
    if auto_select_llm:
        console.print("[blue]🤖 Running automatic LLM selection...[/blue]")
        try:
            selector = AutoLLMSelector(job_id, verbose)
            selection_result = selector.auto_select_best_llm()
            console.print(f"[green]✅ Auto-selected: {selection_result.best_provider.upper()} - {selection_result.best_model}[/green]")
            config = Config()  # Reload config with new selection
        except Exception as e:
            console.print(f"[yellow]⚠️ Auto-selection failed: {e}[/yellow]")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            # STEP 1: Initialize Enhanced Systems
            task1 = progress.add_task("🔧 Initializing enhanced systems...", total=None)
            
            # Initialize role content manager
            role_manager = RoleContentManager()
            
            # Initialize CV monitor
            cv_monitor = CVMonitor(output_dir, role_manager)
            
            # Initialize database profile selector
            profile_selector = DatabaseProfileSelector(role_manager)
            
            # Initialize enhanced DataPM loader
            datapm_loader = EnhancedDataPMLoader()
            
            # Initialize user profile manager (for backward compatibility)
            user_profile_manager = UserProfileManager()
            
            progress.update(task1, completed=True)

            # STEP 2: CV Monitoring and Database Sync
            task2 = progress.add_task("📂 Scanning for CV changes and syncing database...", total=None)
            
            if force_sync:
                console.print("[blue]🔄 Forcing full database synchronization...[/blue]")
                sync_results = cv_monitor.force_full_sync()
            else:
                # Scan for changes
                new_files, modified_files, deleted_files = cv_monitor.scan_for_changes()
                
                if new_files or modified_files or deleted_files:
                    console.print(f"[yellow]📊 Changes detected: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted[/yellow]")
                    
                    # Sync changes
                    files_to_sync = new_files + modified_files
                    if files_to_sync:
                        sync_results = cv_monitor.sync_with_database(files_to_sync)
                        console.print(f"[green]✅ Database sync: {sync_results['synced']} synced, {sync_results['errors']} errors[/green]")
                    else:
                        console.print("[blue]ℹ️ No files to sync[/blue]")
                else:
                    console.print("[green]✅ No CV changes detected - database is up to date[/green]")
            
            # Display monitoring summary
            monitoring_summary = cv_monitor.get_monitoring_summary()
            console.print(f"[cyan]📈 Database Status: {monitoring_summary['total_files']} CVs tracked, {monitoring_summary['synced_files']} synced[/cyan]")
            
            progress.update(task2, completed=True)

            # STEP 3: Load Complete Job Data from DataPM
            task3 = progress.add_task("📄 Loading complete job data from DataPM...", total=None)
            
            # Get complete job data (basic + scrapped + csv_processed)
            complete_job_data = datapm_loader.get_complete_job_data(job_id)
            
            if not complete_job_data.get('job_title_original'):
                console.print(f"[red]❌ No job data found for ID: {job_id}[/red]")
                return
            
            # Convert to JobData object for compatibility
            job_data = JobData(
                job_id=job_id,
                job_title_original=complete_job_data['job_title_original'],
                company=complete_job_data['company'],
                skills=complete_job_data['skills'],
                software=complete_job_data['software']
            )
            
            # Display data completeness
            completeness = complete_job_data['data_completeness']
            completeness_color = "green" if completeness > 0.8 else "yellow" if completeness > 0.5 else "red"
            console.print(f"[{completeness_color}]📊 Data completeness: {completeness:.1%}[/{completeness_color}]")
            
            # Show data sources
            sources = complete_job_data['data_sources']
            console.print(f"[cyan]🔗 Data sources: Basic({sources['basic_data']}), Description({sources['description_source']}), Skills({sources['skills_source']})[/cyan]")
            
            progress.update(task3, completed=True)

            # STEP 4: Select Best Profile from Database
            task4 = progress.add_task("🎯 Selecting best profile from role database...", total=None)
            
            # Select best profile using database instead of DOCX files
            profile_selection = profile_selector.select_best_profile(job_data)
            
            selected_role = profile_selection['selected_role']
            confidence = profile_selection['confidence_score']
            profile_data = profile_selection['profile_data']
            
            confidence_color = "green" if confidence > 0.7 else "yellow" if confidence > 0.4 else "red"
            console.print(f"[{confidence_color}]🎯 Selected Profile: {selected_role} (confidence: {confidence:.2f})[/{confidence_color}]")
            
            # Display profile richness
            if profile_data:
                console.print(f"[cyan]📊 Profile Data: {len(profile_data.get('bullet_points', []))} bullets, {len(profile_data.get('skills', []))} skills, {profile_data.get('cv_count', 0)} CVs[/cyan]")
            
            progress.update(task4, completed=True)

            # STEP 5: Generate Content Using Selected Profile + Job Context
            task5 = progress.add_task("✍️ Generating content with enhanced context...", total=None)
            
            # Determine what to generate
            if cv_only or cover_letter_only:
                both = False
            generate_cv = cv_only or both
            generate_cover_letter = cover_letter_only or both

            # Initialize content generator with enhanced data
            generator = ContentGenerator(
                config.llm_config,
                str(config.datapm_path),
                str(config.templates_path),
                user_profile_manager=user_profile_manager
            )

            if generate_cv:
                # Generate replacements using enhanced context
                replacements = generator.generate_replacements_with_enhanced_context(
                    job_data=job_data,
                    complete_job_data=complete_job_data,
                    selected_profile=profile_data,
                    role_context=complete_job_data.get('role_context', ''),
                    job_description_summary=complete_job_data.get('job_description_summary', '')
                )
                
                # Validate content
                validator = ContentValidator(config)
                validation_result = validator.validate_replacements(replacements)
                
                if not validation_result.is_valid:
                    console.print(f"[red]❌ Content validation failed: {validation_result.error_message}[/red]")
                    return
                
                console.print("[green]✅ Content validation passed[/green]")
            else:
                # Create minimal replacements for cover letter only
                replacements = Replacements(
                    profile_summary=ReplacementBlock(placeholder="ProfileSummary", content="", confidence=0.5),
                    top_bullets=[],
                    skill_list=ReplacementBlock(placeholder="SkillList", content=[], confidence=0.5),
                    software_list=ReplacementBlock(placeholder="SoftwareList", content=[], confidence=0.5),
                    objective_title=ReplacementBlock(placeholder="ObjectiveTitle", content=complete_job_data.get('job_title_short', ''), confidence=1.0),
                    ats_recommendations=ReplacementBlock(placeholder="ATSRecommendations", content="", confidence=0.5),
                    job_id=job_id,
                    company=job_data.company,
                    position=job_data.job_title_original,
                    generated_at=datetime.now().isoformat()
                )

            progress.update(task5, completed=True)

            # STEP 6: Generate CV if requested
            if generate_cv:
                task6 = progress.add_task("📄 Generating CV document...", total=None)
                
                # Use the best available template (could be from selected profile)
                template_path = config.templates_path / "cv_template_example.docx"
                
                # Process CV
                processor = DocxProcessor(str(template_path))
                output_file = processor.process_cv_with_replacements(
                    replacements, 
                    output_path,
                    complete_job_data.get('job_title_short', job_data.job_title_original)
                )
                
                console.print(f"[green]📄 CV generated: {output_file.name}[/green]")
                progress.update(task6, completed=True)

            # STEP 7: Generate Cover Letter if requested
            if generate_cover_letter:
                task7 = progress.add_task("📝 Generating cover letter...", total=None)
                
                cover_letter_gen = CoverLetterGenerator(config.llm_config, str(config.datapm_path))
                
                # Use enhanced job context for cover letter
                cv_content = {
                    'profile_summary': str(replacements.profile_summary.content) if generate_cv else profile_data.get('summary', ''),
                    'skill_list': ', '.join(replacements.skill_list.content) if generate_cv and isinstance(replacements.skill_list.content, list) else ', '.join(profile_data.get('skills', [])),
                    'software_list': ', '.join(replacements.software_list.content) if generate_cv and isinstance(replacements.software_list.content, list) else ', '.join(profile_data.get('software', []))
                }
                
                # Generate with enhanced context
                cover_letter_content = cover_letter_gen.generate_cover_letter_with_context(
                    job_data, 
                    cv_content,
                    job_description_full=complete_job_data.get('job_description_full', ''),
                    role_context=complete_job_data.get('role_context', ''),
                    company_context=complete_job_data.get('company_context', '')
                )
                
                # Save cover letter
                cover_letter_filename = NamingUtils.generate_filename(
                    job_data.job_title_original,
                    job_data.software,
                    job_data.company,
                    "cover_letter"
                )
                
                cv_folder = NamingUtils.find_most_recent_cv_folder(output_path, cover_letter_filename)
                if cv_folder == output_path:
                    job_category = selected_role.replace(' ', '_').lower()
                    cv_folder = output_path / job_category
                    cv_folder.mkdir(exist_ok=True)
                
                cover_letter_file = cv_folder / cover_letter_filename
                cover_letter_file = _save_text_without_overwrite(cover_letter_file, cover_letter_content)
                
                console.print(f"[green]📝 Cover letter generated: {cover_letter_file.name}[/green]")
                progress.update(task7, completed=True)

            # STEP 8: Update Role Database with Success
            task8 = progress.add_task("💾 Updating role database with results...", total=None)
            
            # Record successful generation in role database
            if generate_cv and replacements:
                role_manager.add_cv_content(
                    role_name=selected_role,
                    summary=str(replacements.profile_summary.content),
                    bullet_points=[str(bullet.content) for bullet in replacements.top_bullets],
                    skills=list(replacements.skill_list.content) if isinstance(replacements.skill_list.content, list) else [],
                    software=list(replacements.software_list.content) if isinstance(replacements.software_list.content, list) else [],
                    success_score=confidence
                )
                
                console.print(f"[green]💾 Role database updated for {selected_role}[/green]")
            
            progress.update(task8, completed=True)

        # Final summary
        console.print("\n[bold green]✅ CVPilot Enhanced execution completed successfully![/bold green]")
        
        # Display final stats
        final_table = Table(title="Execution Summary")
        final_table.add_column("Component", style="cyan")
        final_table.add_column("Status", style="green")
        final_table.add_column("Details")
        
        final_table.add_row("Job Data", "✅ Loaded", f"Completeness: {completeness:.1%}")
        final_table.add_row("Profile Selection", "✅ Selected", f"{selected_role} (confidence: {confidence:.2f})")
        final_table.add_row("CV Generation", "✅ Generated" if generate_cv else "⏭️ Skipped", "")
        final_table.add_row("Cover Letter", "✅ Generated" if generate_cover_letter else "⏭️ Skipped", "")
        final_table.add_row("Database Update", "✅ Updated", f"Role: {selected_role}")
        
        console.print(final_table)

    except Exception as e:
        console.print(f"[red]❌ Error during execution: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise

if __name__ == "__main__":
    main()

