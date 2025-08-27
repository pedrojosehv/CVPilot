"""
Template Learning System - Machine Learning for Template Selection
CVPilot - Learns from user selections and improves template recommendations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np

@dataclass
class SelectionHistory:
    """Tracks user template selections for learning"""
    job_id: str
    job_title: str
    selected_template: str
    user_rating: Optional[float] = None  # 1-5 stars
    auto_selected: bool = False
    selection_score: float = 0.0
    timestamp: str = ""
    outcome: Optional[str] = None  # "success", "modified", "rejected"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class SuccessfulSummary:
    """Tracks successful summaries for reuse"""
    summary_text: str
    job_title: str
    industry: str
    role_type: str
    success_score: float = 1.0  # Based on fit score improvement
    usage_count: int = 0
    created_at: str = ""
    last_used: Optional[str] = None
    fit_score_improvement: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class TemplatePerformance:
    """Tracks performance metrics for each template"""
    template_path: str
    total_selections: int = 0
    user_ratings: List[float] = None
    success_rate: float = 0.0
    avg_user_rating: float = 0.0
    role_performance: Dict[str, float] = None
    skill_performance: Dict[str, float] = None
    last_used: Optional[str] = None

    def __post_init__(self):
        if self.user_ratings is None:
            self.user_ratings = []
        if self.role_performance is None:
            self.role_performance = {}
        if self.skill_performance is None:
            self.skill_performance = {}

class TemplateLearningSystem:
    """Machine learning system that learns from user template selections"""

    def __init__(self, data_dir: str = "./data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.history_file = self.data_dir / "selection_history.json"
        self.performance_file = self.data_dir / "template_performance.json"
        self.successful_summaries_file = self.data_dir / "successful_summaries.json"
        self.logger = logging.getLogger(__name__)

        # Learning parameters
        self.min_samples_for_learning = 3  # Minimum selections before learning kicks in
        self.decay_factor = 0.95  # How much older selections are weighted
        self.confidence_threshold = 0.7  # Minimum confidence for ML suggestions
        self.min_fit_improvement = 0.05  # Minimum fit score improvement to consider successful

        # Load existing data
        self.selection_history = self._load_selection_history()
        self.template_performance = self._load_template_performance()
        self.successful_summaries = self._load_successful_summaries()

    def record_selection(self, job_data: Dict[str, Any], selected_template: str,
                        auto_selected: bool = False, selection_score: float = 0.0,
                        user_rating: Optional[float] = None, outcome: Optional[str] = None):
        """Record a template selection for learning"""

        history_entry = SelectionHistory(
            job_id=str(job_data.get('job_id', '')),
            job_title=job_data.get('job_title_original', ''),
            selected_template=selected_template,
            user_rating=user_rating,
            auto_selected=auto_selected,
            selection_score=selection_score,
            outcome=outcome
        )

        self.selection_history.append(history_entry)
        self._update_template_performance(history_entry, job_data)
        self._save_data()

        self.logger.info(f"📚 Recorded selection: {selected_template} for job {job_data.get('job_title_original', '')}")

    def get_ml_recommendation(self, job_data: Dict[str, Any], candidate_templates: List[Any]) -> Optional[Tuple[str, float, str]]:
        """
        Get ML-powered recommendation based on historical performance

        Returns:
            Tuple of (template_path, confidence_score, explanation)
        """
        if len(self.selection_history) < self.min_samples_for_learning:
            return None

        job_title = job_data.get('job_title_original', '').lower()
        job_skills = set(job_data.get('skills', []))
        job_software = set(job_data.get('software', []))

        best_template = None
        best_score = 0.0
        best_reason = ""

        for candidate in candidate_templates:
            template_path = str(candidate.file_path)

            # Get base scoring from current system
            base_score = candidate.score

            # Get ML performance boost
            ml_boost, ml_reason = self._calculate_ml_boost(template_path, job_title, job_skills, job_software)

            # Combine scores
            total_score = base_score * 0.7 + ml_boost * 0.3  # 70% base, 30% ML

            if total_score > best_score and total_score >= self.confidence_threshold:
                best_score = total_score
                best_template = template_path
                best_reason = f"ML Boost: {ml_reason} | Base Score: {base_score:.2f}"

        if best_template:
            return (best_template, best_score, best_reason)

        return None

    def _calculate_ml_boost(self, template_path: str, job_title: str,
                           job_skills: set, job_software: set) -> Tuple[float, str]:
        """Calculate ML performance boost for a template"""

        if template_path not in self.template_performance:
            return (0.0, "No historical data")

        perf = self.template_performance[template_path]

        boost_score = 0.0
        reasons = []

        # 1. Overall performance (30%)
        if perf.total_selections > 0:
            perf_score = perf.success_rate * 0.3
            boost_score += perf_score
            if perf_score > 0.2:
                reasons.append(f"Success rate: {perf.success_rate:.1%}")

        # 2. User ratings (40%)
        if perf.avg_user_rating > 0:
            rating_score = (perf.avg_user_rating / 5.0) * 0.4
            boost_score += rating_score
            if rating_score > 0.2:
                reasons.append(f"Avg rating: {perf.avg_user_rating:.1f}/5")

        # 3. Role-specific performance (30%)
        role_key = self._extract_role_from_title(job_title)
        if role_key in perf.role_performance:
            role_score = perf.role_performance[role_key] * 0.3
            boost_score += role_score
            if role_score > 0.15:
                reasons.append(f"Role performance: {role_score:.1%}")

        reason_text = " | ".join(reasons) if reasons else "Historical performance"

        return (min(boost_score, 1.0), reason_text)

    def _extract_role_from_title(self, job_title: str) -> str:
        """Extract role identifier from job title"""
        title_lower = job_title.lower()

        role_mappings = {
            'product analyst': 'PA',
            'data analyst': 'DA',
            'product manager': 'PM',
            'product owner': 'PO',
            'project manager': 'PJM',
            'business analyst': 'BA'
        }

        for key, value in role_mappings.items():
            if key in title_lower:
                return value

        return 'UNKNOWN'

    def _update_template_performance(self, selection: SelectionHistory, job_data: Dict[str, Any]):
        """Update performance metrics for a template"""

        template_path = selection.selected_template

        if template_path not in self.template_performance:
            self.template_performance[template_path] = TemplatePerformance(template_path=template_path)

        perf = self.template_performance[template_path]

        # Update basic metrics
        perf.total_selections += 1
        perf.last_used = selection.timestamp

        if selection.user_rating:
            perf.user_ratings.append(selection.user_rating)
            perf.avg_user_rating = np.mean(perf.user_ratings)

        # Update success rate
        if selection.outcome == "success":
            perf.success_rate = (perf.success_rate * (perf.total_selections - 1) + 1) / perf.total_selections
        elif selection.outcome in ["modified", "rejected"]:
            perf.success_rate = (perf.success_rate * (perf.total_selections - 1)) / perf.total_selections

        # Update role-specific performance
        role_key = self._extract_role_from_title(job_data.get('job_title_original', ''))
        if role_key not in perf.role_performance:
            perf.role_performance[role_key] = 0.0

        # Simple moving average for role performance
        if selection.outcome == "success":
            perf.role_performance[role_key] = (perf.role_performance[role_key] + 1) / 2
        elif selection.outcome in ["modified", "rejected"]:
            perf.role_performance[role_key] = perf.role_performance[role_key] / 2

    def _load_selection_history(self) -> List[SelectionHistory]:
        """Load selection history from file"""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [SelectionHistory(**item) for item in data]
        except Exception as e:
            self.logger.error(f"Error loading selection history: {e}")
            return []

    def _load_template_performance(self) -> Dict[str, TemplatePerformance]:
        """Load template performance data from file"""
        if not self.performance_file.exists():
            return {}

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result = {}
                for key, value in data.items():
                    # Convert nested dicts back to proper format
                    if 'user_ratings' in value and isinstance(value['user_ratings'], list):
                        value['user_ratings'] = value['user_ratings']
                    if 'role_performance' in value and isinstance(value['role_performance'], dict):
                        value['role_performance'] = value['role_performance']
                    if 'skill_performance' in value and isinstance(value['skill_performance'], dict):
                        value['skill_performance'] = value['skill_performance']
                    result[key] = TemplatePerformance(**value)
                return result
        except Exception as e:
            self.logger.error(f"Error loading template performance: {e}")
            return {}

    def _save_data(self):
        """Save all learning data to files"""
        try:
            # Save selection history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(item) for item in self.selection_history], f, indent=2, ensure_ascii=False)

            # Save template performance
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump({k: asdict(v) for k, v in self.template_performance.items()},
                         f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics"""
        total_selections = len(self.selection_history)
        templates_with_ratings = len([p for p in self.template_performance.values() if p.user_ratings])
        avg_rating = np.mean([p.avg_user_rating for p in self.template_performance.values()
                             if p.avg_user_rating > 0]) if templates_with_ratings > 0 else 0

        return {
            'total_selections': total_selections,
            'templates_tracked': len(self.template_performance),
            'templates_with_ratings': templates_with_ratings,
            'average_rating': round(avg_rating, 2) if avg_rating > 0 else 0,
            'learning_active': total_selections >= self.min_samples_for_learning
        }

    def record_successful_summary(self, summary_text: str, job_data: Dict[str, Any],
                                 fit_score_improvement: float, role_type: str = None):
        """Record a successful summary for future reuse"""

        if fit_score_improvement < self.min_fit_improvement:
            return  # Only record significantly successful summaries

        if not role_type:
            role_type = self._extract_role_from_title(job_data.get('job_title_original', ''))

        industry = self._infer_industry_from_job_data(job_data)

        successful_summary = SuccessfulSummary(
            summary_text=summary_text,
            job_title=job_data.get('job_title_original', ''),
            industry=industry,
            role_type=role_type,
            success_score=fit_score_improvement,
            fit_score_improvement=fit_score_improvement
        )

        self.successful_summaries.append(successful_summary)
        self._save_successful_summaries()

        self.logger.info(f"💡 Recorded successful summary for {role_type} role in {industry} industry")

    def find_similar_successful_summary(self, job_data: Dict[str, Any], min_similarity: float = 0.6) -> Optional[str]:
        """Find a similar successful summary to reuse"""

        if len(self.successful_summaries) < self.min_samples_for_learning:
            return None

        target_role = self._extract_role_from_title(job_data.get('job_title_original', ''))
        target_industry = self._infer_industry_from_job_data(job_data)
        target_skills = set(job_data.get('skills', []))
        target_software = set(job_data.get('software', []))

        best_match = None
        best_score = 0.0

        for summary in self.successful_summaries:
            # Calculate similarity score
            similarity = self._calculate_summary_similarity(
                summary, target_role, target_industry, target_skills, target_software
            )

            if similarity > min_similarity and similarity > best_score:
                best_score = similarity
                best_match = summary.summary_text

                # Update usage statistics
                summary.usage_count += 1
                summary.last_used = datetime.now().isoformat()

        if best_match:
            self._save_successful_summaries()
            self.logger.info(f"🔄 Reusing successful summary (similarity: {best_score:.2f})")

        return best_match

    def _calculate_summary_similarity(self, summary: SuccessfulSummary, target_role: str,
                                    target_industry: str, target_skills: set, target_software: set) -> float:
        """Calculate how similar a stored summary is to the current job requirements"""

        score = 0.0
        total_weight = 0.0

        # Role match (40% weight)
        if summary.role_type == target_role:
            score += 0.4
        elif summary.role_type != 'UNKNOWN':
            score += 0.1  # Partial credit for related roles
        total_weight += 0.4

        # Industry match (30% weight)
        if summary.industry == target_industry:
            score += 0.3
        total_weight += 0.3

        # Skills overlap (20% weight)
        summary_skills = set(summary.summary_text.lower().split())
        skill_overlap = len(target_skills.intersection(summary_skills)) / max(len(target_skills), 1)
        score += skill_overlap * 0.2
        total_weight += 0.2

        # Software/tools overlap (10% weight)
        summary_software = set(summary.summary_text.lower().split())
        software_overlap = len(target_software.intersection(summary_software)) / max(len(target_software), 1)
        score += software_overlap * 0.1
        total_weight += 0.1

        # Age penalty (older summaries get slightly lower scores)
        days_old = (datetime.now() - datetime.fromisoformat(summary.created_at)).days
        age_penalty = min(days_old / 365, 0.2)  # Max 20% penalty for very old summaries
        score *= (1 - age_penalty)

        # Success score bonus
        success_bonus = min(summary.success_score, 0.3)  # Max 30% bonus
        score *= (1 + success_bonus)

        return score / total_weight if total_weight > 0 else 0.0

    def _infer_industry_from_job_data(self, job_data: Dict[str, Any]) -> str:
        """Infer industry from job data"""
        company = job_data.get('company', '').lower()
        title = job_data.get('job_title_original', '').lower()
        skills = ' '.join(job_data.get('skills', [])).lower()

        text_to_analyze = f"{company} {title} {skills}"

        industry_keywords = {
            "Technology/SaaS": ["saas", "software", "cloud", "digital", "platform", "api", "web", "mobile", "tech"],
            "Manufacturing": ["manufacturing", "production", "industrial", "supply chain", "factory"],
            "Financial Services": ["financial", "fintech", "banking", "payment", "trading", "investment"],
            "Healthcare": ["healthcare", "medical", "clinical", "patient", "pharma", "biotech"],
            "Retail/E-commerce": ["retail", "ecommerce", "customer", "sales", "commerce"],
            "Consulting": ["consulting", "advisory", "strategy", "transformation"],
            "Business Operations": ["operations", "business", "management", "process"]
        }

        for industry, keywords in industry_keywords.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                return industry

        return "Business Operations"  # Default

    def _load_successful_summaries(self) -> List[SuccessfulSummary]:
        """Load successful summaries from file"""
        if not self.successful_summaries_file.exists():
            return []

        try:
            with open(self.successful_summaries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [SuccessfulSummary(**item) for item in data]
        except Exception as e:
            self.logger.error(f"Error loading successful summaries: {e}")
            return []

    def _save_successful_summaries(self):
        """Save successful summaries to file"""
        try:
            with open(self.successful_summaries_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(item) for item in self.successful_summaries],
                         f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving successful summaries: {e}")

    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        base_stats = self.get_statistics()

        summary_stats = {
            'successful_summaries_count': len(self.successful_summaries),
            'summaries_by_role': defaultdict(int),
            'summaries_by_industry': defaultdict(int),
            'avg_fit_improvement': 0.0,
            'most_successful_role': None,
            'most_successful_industry': None
        }

        if self.successful_summaries:
            total_improvement = sum(s.fit_score_improvement for s in self.successful_summaries)
            summary_stats['avg_fit_improvement'] = total_improvement / len(self.successful_summaries)

            for summary in self.successful_summaries:
                summary_stats['summaries_by_role'][summary.role_type] += 1
                summary_stats['summaries_by_industry'][summary.industry] += 1

            summary_stats['most_successful_role'] = max(summary_stats['summaries_by_role'],
                                                      key=summary_stats['summaries_by_role'].get)
            summary_stats['most_successful_industry'] = max(summary_stats['summaries_by_industry'],
                                                           key=summary_stats['summaries_by_industry'].get)

        return {**base_stats, **summary_stats}
