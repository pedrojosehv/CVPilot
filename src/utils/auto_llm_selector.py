"""
Auto LLM Selector - Intelligent automatic selection of best available LLM
CVPilot - Automatically tests and selects the best performing model
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json

# Import for loading DataPM keys
from ..utils.api_key_manager import get_api_key

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ..generation.content_generator import ContentGenerator
from ..utils.models import JobData, MatchResult, LLMConfig
from .model_selector import ModelSelector

console = Console()

@dataclass
class ModelTestResult:
    """Result of testing a specific model"""
    provider: str
    model: str
    display_name: str
    available: bool
    response_time: float
    quality_score: float
    summary_generated: str
    error_message: Optional[str] = None
    api_working: bool = True

@dataclass
class AutoSelectionResult:
    """Final result of automatic model selection"""
    best_model: str
    best_provider: str
    best_score: float
    tested_models: List[ModelTestResult]
    recommendation_reason: str
    timestamp: str

class AutoLLMSelector:
    """Intelligent automatic LLM selection based on availability and quality"""

    def __init__(self, test_job_id: str = "159", verbose: bool = True):
        self.test_job_id = test_job_id
        self.verbose = verbose
        self.results_dir = Path("./data/llm_tests")
        self.results_dir.mkdir(exist_ok=True, parents=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO if verbose else logging.WARNING)

    def auto_select_best_llm(self) -> AutoSelectionResult:
        """
        Automatically test available LLMs and select the best one

        Returns:
            AutoSelectionResult with the best model and test results
        """

        console.print("[bold blue]🚀 AUTO LLM SELECTION STARTING[/bold blue]")
        console.print("[bold cyan]Testing available models and selecting the best performer[/bold cyan]")
        console.print("=" * 70)

        # Step 1: Discover available models
        console.print("\n[cyan]1. 🔍 Discovering Available Models...[/cyan]")
        available_models = self._discover_available_models()

        if not available_models:
            raise ValueError("❌ No LLM models available! Please check your API keys.")

        console.print(f"   ✅ Found {len(available_models)} models to test")

        # Step 2: Prepare test data
        console.print("\n[cyan]2. 📋 Preparing Test Data...[/cyan]")
        test_data = self._prepare_test_data()
        console.print("   ✅ Test data prepared")

        # Step 3: Test each model
        console.print(f"\n[cyan]3. 🧪 Testing {len(available_models)} Models...[/cyan]")
        test_results = self._test_all_models(available_models, test_data)

        # Step 4: Analyze results and select best
        console.print("\n[cyan]4. 📊 Analyzing Results...[/cyan]")
        best_result, analysis = self._analyze_results(test_results)

        # Step 5: Apply selection
        console.print(f"\n[cyan]5. 🎯 Applying Best Model Selection...[/cyan]")
        self._apply_selection(best_result)

        # Step 6: Save results
        selection_result = AutoSelectionResult(
            best_model=best_result.model,
            best_provider=best_result.provider,
            best_score=best_result.quality_score,
            tested_models=test_results,
            recommendation_reason=analysis['reason'],
            timestamp=datetime.now().isoformat()
        )

        self._save_results(selection_result)

        # Display final results
        self._display_final_results(selection_result, analysis)

        return selection_result

    def _discover_available_models(self) -> List[Dict[str, Any]]:
        """Discover which models are available based on API keys"""

        available_models = []

        # Check OpenAI (optional)
        if os.getenv("OPENAI_API_KEY"):
            available_models.extend([
                {'provider': 'openai', 'model': 'gpt-4o', 'name': 'GPT-4o (OpenAI)'},
                {'provider': 'openai', 'model': 'gpt-4-turbo', 'name': 'GPT-4 Turbo (OpenAI)'},
            ])
            self.logger.info("✅ OpenAI models available")

        # Check Anthropic (optional)
        if os.getenv("ANTHROPIC_API_KEY"):
            available_models.extend([
                {'provider': 'anthropic', 'model': 'claude-3-5-sonnet', 'name': 'Claude 3.5 Sonnet (Anthropic)'},
                {'provider': 'anthropic', 'model': 'claude-3-opus', 'name': 'Claude 3 Opus (Anthropic)'},
            ])
            self.logger.info("✅ Anthropic models available")

        # Check Gemini (primary option since user has these keys)
        gemini_keys = os.getenv("GEMINI_API_KEYS", "")
        if not gemini_keys:
            # Try loading from DataPM file (this is how the user has their keys)
            datapm_api_file = Path("D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt")
            if datapm_api_file.exists():
                try:
                    with open(datapm_api_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                        if keys:
                            gemini_keys = ",".join(keys)
                            self.logger.info(f"✅ Loaded {len(keys)} Gemini API keys from DataPM")
                except Exception as e:
                    self.logger.warning(f"Could not load Gemini keys from DataPM: {e}")

        if gemini_keys:
            available_models.extend([
                {'provider': 'gemini', 'model': 'gemini-1-5-pro', 'name': 'Gemini 1.5 Pro (Google)'},
                {'provider': 'gemini', 'model': 'gemini-1-5-flash', 'name': 'Gemini 1.5 Flash (Google)'},
            ])
            self.logger.info(f"✅ Gemini models available: {len([m for m in available_models if m['provider'] == 'gemini'])} models")

        return available_models

    def _prepare_test_data(self) -> Dict[str, Any]:
        """Prepare test data for model evaluation"""

        # Use a real job from the system for testing
        try:
            from ..ingest.manual_loader import ManualLoader
            from pathlib import Path

            config_path = Path("./src/utils/config.py")
            # We'll create a simple test job instead
            test_job = JobData(
                job_id="test_quality",
                job_title_original="Business Operations Specialist",
                job_title_short="Business Operations",
                company="TechCorp",
                country="Spain",
                skills=["SQL", "Oracle", "Python", "Excel", "Tableau"],
                software=["SQL Server", "Oracle Database", "Power BI"],
                experience_years="3-5"
            )

            match_result = MatchResult(
                matched_skills=["SQL", "Oracle", "Python"],
                fit_score=0.85,
                confidence=0.9,
                matched_keywords=["business operations", "data analysis", "process optimization"],
                missing_skills=["Advanced Excel"],
                recommendations=["Strong technical foundation"]
            )

            return {
                'job_data': test_job,
                'match_result': match_result
            }

        except Exception as e:
            self.logger.warning(f"Could not load test job: {e}")
            # Fallback to synthetic data
            return self._create_synthetic_test_data()

    def _create_synthetic_test_data(self) -> Dict[str, Any]:
        """Create synthetic test data if real data is not available"""

        test_job = JobData(
            job_id="synthetic_test",
            job_title_original="Senior Business Operations Analyst",
            job_title_short="Business Operations Analyst",
            company="Innovative Solutions Inc",
            country="United States",
            skills=["SQL", "Python", "Tableau", "Excel", "Power BI"],
            software=["PostgreSQL", "Tableau Desktop", "Microsoft Excel"],
            experience_years="4-6"
        )

        match_result = MatchResult(
            matched_skills=["SQL", "Python", "Tableau"],
            fit_score=0.8,
            confidence=0.85,
            matched_keywords=["business operations", "data analysis", "reporting"],
            missing_skills=["Advanced Python"],
            recommendations=["Excellent technical skills match"]
        )

        return {
            'job_data': test_job,
            'match_result': match_result
        }

    def _test_all_models(self, available_models: List[Dict[str, Any]],
                        test_data: Dict[str, Any]) -> List[ModelTestResult]:
        """Test all available models and collect results"""

        test_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=not self.verbose
        ) as progress:

            main_task = progress.add_task("Testing LLM models...", total=len(available_models))

            for model_config in available_models:
                model_task = progress.add_task(
                    f"Testing {model_config['name']}...",
                    total=1
                )

                try:
                    result = self._test_single_model(model_config, test_data)
                    test_results.append(result)

                    if result.available and result.api_working:
                        progress.update(model_task, completed=1,
                                      description=f"✅ {model_config['name']} - Quality: {result.quality_score:.2f}")
                    else:
                        progress.update(model_task, completed=1,
                                      description=f"❌ {model_config['name']} - {result.error_message}")

                except Exception as e:
                    error_result = ModelTestResult(
                        provider=model_config['provider'],
                        model=model_config['model'],
                        display_name=model_config['name'],
                        available=False,
                        response_time=0.0,
                        quality_score=0.0,
                        summary_generated="",
                        error_message=str(e),
                        api_working=False
                    )
                    test_results.append(error_result)
                    progress.update(model_task, completed=1,
                                  description=f"❌ {model_config['name']} - Error: {str(e)[:50]}...")

                progress.update(main_task, advance=1)

        return test_results

    def _test_single_model(self, model_config: Dict[str, Any],
                          test_data: Dict[str, Any]) -> ModelTestResult:
        """Test a single model and return results"""

        start_time = time.time()

        try:
            # Create LLM config
            llm_config = LLMConfig(
                provider=model_config['provider'],
                model=model_config['model'],
                temperature=0.7,
                max_tokens=300
            )

            # Create content generator
            generator = ContentGenerator(
                llm_config=llm_config,
                datapm_path=None,  # Skip datapm for testing
                templates_path=None  # Skip templates for testing
            )

            # Generate summary
            replacements = generator.generate_replacements(
                test_data['job_data'],
                test_data['match_result']
            )

            summary = replacements.blocks[0].content
            response_time = time.time() - start_time

            # Calculate quality score
            quality_score = generator._calculate_summary_quality(summary, test_data['job_data'])

            return ModelTestResult(
                provider=model_config['provider'],
                model=model_config['model'],
                display_name=model_config['name'],
                available=True,
                response_time=response_time,
                quality_score=quality_score,
                summary_generated=summary,
                api_working=True
            )

        except Exception as e:
            return ModelTestResult(
                provider=model_config['provider'],
                model=model_config['model'],
                display_name=model_config['name'],
                available=False,
                response_time=time.time() - start_time,
                quality_score=0.0,
                summary_generated="",
                error_message=str(e),
                api_working=False
            )

    def _analyze_results(self, test_results: List[ModelTestResult]) -> Tuple[ModelTestResult, Dict[str, Any]]:
        """Analyze test results and select the best model"""

        # Filter working models
        working_models = [r for r in test_results if r.available and r.api_working]

        if not working_models:
            raise ValueError("❌ No working LLM models found!")

        # Select best model based on quality score
        best_result = max(working_models, key=lambda x: x.quality_score)

        # Create analysis
        analysis = {
            'total_tested': len(test_results),
            'working_models': len(working_models),
            'best_score': best_result.quality_score,
            'average_score': sum(r.quality_score for r in working_models) / len(working_models),
            'reason': self._generate_reasoning(best_result, working_models)
        }

        return best_result, analysis

    def _generate_reasoning(self, best_result: ModelTestResult,
                           all_results: List[ModelTestResult]) -> str:
        """Generate human-readable reasoning for the selection"""

        reasons = []

        if best_result.quality_score >= 0.8:
            reasons.append("exceptional quality")
        elif best_result.quality_score >= 0.7:
            reasons.append("very good quality")
        elif best_result.quality_score >= 0.6:
            reasons.append("good quality")
        else:
            reasons.append("acceptable quality")

        # Compare with others
        better_than_others = len([r for r in all_results if r.quality_score < best_result.quality_score])
        if better_than_others > 0:
            reasons.append(f"outperformed {better_than_others} other model(s)")

        # Response time consideration
        avg_time = sum(r.response_time for r in all_results) / len(all_results)
        if best_result.response_time < avg_time * 0.8:
            reasons.append("fast response time")
        elif best_result.response_time > avg_time * 1.5:
            reasons.append("(slower but highest quality)")

        return ", ".join(reasons).capitalize()

    def _apply_selection(self, best_result: ModelTestResult):
        """Apply the selected model configuration"""

        # Set environment variables
        os.environ["LLM_PROVIDER"] = best_result.provider
        os.environ["LLM_MODEL"] = best_result.model

        console.print(f"[green]✅ Selected: {best_result.display_name}[/green]")
        console.print(f"[cyan]   Quality Score: {best_result.quality_score:.2f}[/cyan]")
        console.print(f"[cyan]   Response Time: {best_result.response_time:.2f}s[/cyan]")

    def _save_results(self, result: AutoSelectionResult):
        """Save test results for future reference"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"llm_selection_{timestamp}.json"

        # Convert to serializable format
        serializable_result = {
            'best_model': result.best_model,
            'best_provider': result.best_provider,
            'best_score': result.best_score,
            'recommendation_reason': result.recommendation_reason,
            'timestamp': result.timestamp,
            'tested_models': [
                {
                    'provider': r.provider,
                    'model': r.model,
                    'display_name': r.display_name,
                    'available': r.available,
                    'response_time': r.response_time,
                    'quality_score': r.quality_score,
                    'error_message': r.error_message,
                    'api_working': r.api_working
                }
                for r in result.tested_models
            ]
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False, default=str)

        console.print(f"[dim]💾 Results saved to: {results_file}[/dim]")

    def _display_final_results(self, result: AutoSelectionResult, analysis: Dict[str, Any]):
        """Display final selection results in a nice format"""

        # Summary table
        table = Table(title="🤖 Auto LLM Selection Results")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", width=30)

        table.add_row("Selected Model", f"{result.best_provider.upper()} - {result.best_model}")
        table.add_row("Quality Score", f"{result.best_score:.3f}")
        table.add_row("Reason", result.recommendation_reason)
        table.add_row("Models Tested", str(analysis['total_tested']))
        table.add_row("Working Models", str(analysis['working_models']))
        table.add_row("Average Score", f"{analysis['average_score']:.3f}")

        console.print(f"\n{table}")

        # Best summary preview
        best_model_result = next((r for r in result.tested_models
                                if r.model == result.best_model and r.provider == result.best_provider), None)

        if best_model_result and best_model_result.summary_generated:
            console.print(f"\n[bold green]📝 Best Summary Preview:[/bold green]")
            preview_panel = Panel(
                best_model_result.summary_generated[:200] + "..." if len(best_model_result.summary_generated) > 200 else best_model_result.summary_generated,
                title=f"Generated by {best_model_result.display_name}",
                border_style="green"
            )
            console.print(preview_panel)

        console.print(f"\n[bold green]🎉 Auto-selection complete![/bold green]")
        console.print(f"[green]The system is now using the best available LLM for CV generation.[/green]")

def run_auto_selection(test_job_id: str = "159", verbose: bool = True) -> AutoSelectionResult:
    """Convenience function to run auto-selection"""
    selector = AutoLLMSelector(test_job_id, verbose)
    return selector.auto_select_best_llm()

if __name__ == "__main__":
    run_auto_selection()
