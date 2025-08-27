"""
Model Selector - Utility for selecting optimal modern LLM models
CVPilot - Helps choose the best model based on requirements
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()

@dataclass
class ModelRecommendation:
    """Recommendation for a specific model"""
    provider: str
    model: str
    display_name: str
    description: str
    use_case: str
    quality_score: float
    speed_score: float
    cost_score: float

class ModelSelector:
    """Utility for selecting optimal modern LLM models"""

    def __init__(self):
        self.models = self._get_available_models()

    def _get_available_models(self) -> Dict[str, ModelRecommendation]:
        """Get all available modern models with their characteristics"""

        return {
            'gpt-4o': ModelRecommendation(
                provider='openai',
                model='gpt-4o',
                display_name='GPT-4o (OpenAI)',
                description='Most advanced GPT-4 model with superior reasoning and quality',
                use_case='High-quality content generation, complex analysis',
                quality_score=0.95,
                speed_score=0.8,
                cost_score=0.7
            ),
            'claude-3-5-sonnet': ModelRecommendation(
                provider='anthropic',
                model='claude-3-5-sonnet',
                display_name='Claude 3.5 Sonnet (Anthropic)',
                description='Most advanced Claude model with exceptional analysis capabilities',
                use_case='Creative writing, detailed analysis, professional content',
                quality_score=0.92,
                speed_score=0.85,
                cost_score=0.8
            ),
            'gemini-1-5-pro': ModelRecommendation(
                provider='gemini',
                model='gemini-1-5-pro',
                display_name='Gemini 1.5 Pro (Google)',
                description='Most capable Gemini model with advanced multimodal reasoning',
                use_case='Fast processing, good quality-cost balance',
                quality_score=0.88,
                speed_score=0.9,
                cost_score=0.9
            ),
            'gpt-4-turbo': ModelRecommendation(
                provider='openai',
                model='gpt-4-turbo',
                display_name='GPT-4 Turbo (OpenAI)',
                description='Previous most advanced GPT-4 with good performance',
                use_case='High-quality content with faster processing',
                quality_score=0.9,
                speed_score=0.85,
                cost_score=0.75
            ),
            'claude-3-opus': ModelRecommendation(
                provider='anthropic',
                model='claude-3-opus',
                display_name='Claude 3 Opus (Anthropic)',
                description='Most capable Claude 3 model for complex tasks',
                use_case='Maximum quality for critical applications',
                quality_score=0.93,
                speed_score=0.7,
                cost_score=0.6
            ),
            'gemini-1-5-flash': ModelRecommendation(
                provider='gemini',
                model='gemini-1-5-flash',
                display_name='Gemini 1.5 Flash (Google)',
                description='Fast and efficient Gemini model for quick responses',
                use_case='High-volume processing, cost-effective solutions',
                quality_score=0.82,
                speed_score=0.95,
                cost_score=0.95
            )
        }

    def recommend_model(self, priority: str = "quality", use_case: str = "cv_generation") -> ModelRecommendation:
        """
        Recommend the best model based on priority and use case

        Args:
            priority: 'quality', 'speed', or 'cost'
            use_case: specific use case (cv_generation, creative_writing, analysis)
        """

        if priority == "quality":
            # Return highest quality model
            return max(self.models.values(), key=lambda x: x.quality_score)
        elif priority == "speed":
            # Return fastest model
            return max(self.models.values(), key=lambda x: x.speed_score)
        elif priority == "cost":
            # Return most cost-effective model
            return max(self.models.values(), key=lambda x: x.cost_score)
        else:
            # Default to quality
            return self.models['gpt-4o']

    def list_available_models(self):
        """Display all available models in a table"""

        table = Table(title="🤖 Available Modern LLM Models")
        table.add_column("Model", style="cyan", width=30)
        table.add_column("Provider", style="magenta", width=12)
        table.add_column("Quality", style="green", justify="center")
        table.add_column("Speed", style="yellow", justify="center")
        table.add_column("Cost", style="blue", justify="center")
        table.add_column("Use Case", style="white", width=40)

        for model_key, model in self.models.items():
            table.add_row(
                model.display_name,
                model.provider.title(),
                f"{model.quality_score:.2f}",
                f"{model.speed_score:.2f}",
                f"{model.cost_score:.2f}",
                model.use_case
            )

        console.print(table)

    def get_model_config(self, model_key: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""

        if model_key not in self.models:
            console.print(f"[red]❌ Model '{model_key}' not found[/red]")
            return None

        model = self.models[model_key]
        return {
            'provider': model.provider,
            'model': model.model,
            'display_name': model.display_name,
            'description': model.description
        }

    def interactive_selection(self) -> Optional[ModelRecommendation]:
        """Interactive model selection"""

        console.print("[bold blue]🎯 LLM Model Selection[/bold blue]")
        console.print("Choose the best model for your needs:\n")

        # Show options
        options = {}
        for i, (key, model) in enumerate(self.models.items(), 1):
            console.print(f"[cyan]{i}.[/cyan] {model.display_name}")
            console.print(f"   [dim]{model.description}[/dim]")
            console.print(f"   [green]Quality: {model.quality_score:.2f}[/green] | "
                         f"[yellow]Speed: {model.speed_score:.2f}[/yellow] | "
                         f"[blue]Cost: {model.cost_score:.2f}[/blue]")
            console.print()
            options[str(i)] = model

        # Get user choice
        choice = Prompt.ask("Select a model (1-6)", choices=list(options.keys()))

        selected_model = options[choice]
        console.print(f"\n[green]✅ Selected: {selected_model.display_name}[/green]")
        console.print(f"[dim]{selected_model.description}[/dim]")

        return selected_model

def setup_environment_for_model(model: ModelRecommendation) -> str:
    """Generate environment variable setup commands for the selected model"""

    commands = [
        f"export LLM_PROVIDER={model.provider}",
        f"export LLM_MODEL={model.model}",
        f"# {model.display_name} - {model.description}"
    ]

    console.print("\n[bold cyan]🔧 Environment Setup:[/bold cyan]")
    console.print("Add these lines to your .env file:")
    console.print()

    for cmd in commands:
        if cmd.startswith("#"):
            console.print(f"[dim]{cmd}[/dim]")
        else:
            console.print(f"[green]{cmd}[/green]")

    return "\n".join(commands)

# Quick setup functions for common use cases
def setup_best_quality():
    """Setup for maximum quality"""
    selector = ModelSelector()
    model = selector.recommend_model("quality")
    console.print(f"[green]🎯 Best Quality Setup: {model.display_name}[/green]")
    return setup_environment_for_model(model)

def setup_best_speed():
    """Setup for maximum speed"""
    selector = ModelSelector()
    model = selector.recommend_model("speed")
    console.print(f"[green]⚡ Best Speed Setup: {model.display_name}[/green]")
    return setup_environment_for_model(model)

def setup_best_cost():
    """Setup for best cost-effectiveness"""
    selector = ModelSelector()
    model = selector.recommend_model("cost")
    console.print(f"[green]💰 Best Cost Setup: {model.display_name}[/green]")
    return setup_environment_for_model(model)
