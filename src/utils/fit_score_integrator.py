"""
Fit Score Integrator - Include Original Template Performance
CVPilot - Considers the fit score from when the template was originally created
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import re

class FitScoreIntegrator:
    """Integrates original fit scores from template creation into selection process"""

    def __init__(self, logs_dir: str = "./logs"):
        self.logs_dir = Path(logs_dir)
        self.logger = logging.getLogger(__name__)

        # Cache for parsed log data
        self.fit_score_cache = {}
        self.template_performance = {}

    def get_template_fit_score(self, template_path: Path, job_data: Dict[str, Any]) -> Optional[float]:
        """
        Get the original fit score when this template was created

        Returns:
            Original fit score 0-1, or None if not found
        """
        template_name = template_path.name

        # Try cache first
        if template_name in self.fit_score_cache:
            return self.fit_score_cache[template_name]

        # Parse logs to find original fit score
        fit_score = self._extract_original_fit_score(template_name, job_data)

        # Cache the result
        self.fit_score_cache[template_name] = fit_score

        return fit_score

    def calculate_fit_score_boost(self, template_path: Path, job_data: Dict[str, Any],
                                current_fit_score: float) -> Tuple[float, str]:
        """
        Calculate boost based on original template performance

        Returns:
            Tuple of (boost_score, explanation)
        """
        original_fit = self.get_template_fit_score(template_path, job_data)

        if original_fit is None:
            return (0.0, "No original fit data available")

        # Calculate boost based on original performance
        if original_fit >= 0.8:  # High performing template
            boost = 0.15
            reason = f"Originally high performer ({original_fit:.2f})"
        elif original_fit >= 0.6:  # Good performer
            boost = 0.08
            reason = f"Originally good performer ({original_fit:.2f})"
        elif original_fit >= 0.4:  # Average performer
            boost = 0.0
            reason = f"Originally average performer ({original_fit:.2f})"
        else:  # Low performer
            boost = -0.1  # Penalty
            reason = f"Originally low performer ({original_fit:.2f})"

        return (boost, reason)

    def get_template_success_rate(self, template_path: Path) -> Tuple[float, int]:
        """
        Get success rate and usage count for a template

        Returns:
            Tuple of (success_rate, total_uses)
        """
        template_name = template_path.name

        if template_name not in self.template_performance:
            self._analyze_template_performance(template_name)

        perf = self.template_performance.get(template_name, {'success_rate': 0.0, 'total_uses': 0})

        return (perf['success_rate'], perf['total_uses'])

    def _extract_original_fit_score(self, template_name: str, job_data: Dict[str, Any]) -> Optional[float]:
        """Extract the original fit score from logs when template was created"""

        if not self.logs_dir.exists():
            return None

        # Look for relevant log files
        log_files = list(self.logs_dir.glob("*.log"))
        log_files.extend(list(self.logs_dir.glob("*.txt")))

        if not log_files:
            return None

        # Sort by modification time, newest first
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Search for template creation or first usage
        for log_file in log_files[:10]:  # Check last 10 log files
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    # Look for patterns indicating template creation/usage
                    patterns = [
                        rf"Final fit score: (\d+\.\d+).*?{re.escape(template_name)}",
                        rf"fit_score.*?: (\d+\.\d+).*?{re.escape(template_name)}",
                        rf"Template.*?: {re.escape(template_name)}.*?fit.*?: (\d+\.\d+)"
                    ]

                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            # Take the highest fit score found
                            scores = [float(match) for match in matches]
                            return max(scores) if scores else None

            except Exception as e:
                self.logger.debug(f"Error reading log file {log_file}: {e}")
                continue

        return None

    def _analyze_template_performance(self, template_name: str):
        """Analyze historical performance of a template"""

        if not self.logs_dir.exists():
            self.template_performance[template_name] = {'success_rate': 0.0, 'total_uses': 0}
            return

        success_count = 0
        total_uses = 0

        # Look through logs for template usage
        log_files = list(self.logs_dir.glob("*.log"))
        log_files.extend(list(self.logs_dir.glob("*.txt")))

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    # Count template usages
                    usage_pattern = rf"template.*?: {re.escape(template_name)}"
                    usages = len(re.findall(usage_pattern, content, re.IGNORECASE))

                    if usages > 0:
                        total_uses += usages

                        # Look for success indicators
                        success_pattern = rf"success.*?:.*?{re.escape(template_name)}|completed.*?:.*?{re.escape(template_name)}"
                        successes = len(re.findall(success_pattern, content, re.IGNORECASE))

                        success_count += successes

            except Exception as e:
                self.logger.debug(f"Error analyzing log file {log_file}: {e}")
                continue

        # Calculate success rate
        success_rate = success_count / max(total_uses, 1)

        self.template_performance[template_name] = {
            'success_rate': success_rate,
            'total_uses': total_uses
        }

    def get_performance_insights(self, template_path: Path) -> Dict[str, Any]:
        """Get performance insights for a template"""

        template_name = template_path.name
        success_rate, total_uses = self.get_template_success_rate(template_path)

        insights = {
            'template_name': template_name,
            'total_uses': total_uses,
            'success_rate': success_rate,
            'performance_level': self._categorize_performance(success_rate),
            'recommendation': self._get_performance_recommendation(success_rate, total_uses)
        }

        return insights

    def _categorize_performance(self, success_rate: float) -> str:
        """Categorize template performance level"""
        if success_rate >= 0.8:
            return "Excellent"
        elif success_rate >= 0.6:
            return "Good"
        elif success_rate >= 0.4:
            return "Average"
        elif success_rate >= 0.2:
            return "Below Average"
        else:
            return "Poor"

    def _get_performance_recommendation(self, success_rate: float, total_uses: int) -> str:
        """Get recommendation based on performance"""

        if total_uses < 3:
            return "Insufficient data - needs more usage"
        elif success_rate >= 0.8:
            return "High performer - prioritize for similar jobs"
        elif success_rate >= 0.6:
            return "Good performer - use for appropriate matches"
        elif success_rate >= 0.4:
            return "Average - monitor performance"
        else:
            return "Low performance - consider alternatives or improvement"

    def export_performance_report(self, output_file: str = "template_performance_report.json"):
        """Export comprehensive performance report for all templates"""

        report = {
            'generated_at': datetime.now().isoformat(),
            'templates_analyzed': len(self.template_performance),
            'performance_summary': {}
        }

        for template_name, perf in self.template_performance.items():
            report['performance_summary'][template_name] = {
                'success_rate': perf['success_rate'],
                'total_uses': perf['total_uses'],
                'performance_level': self._categorize_performance(perf['success_rate']),
                'recommendation': self._get_performance_recommendation(perf['success_rate'], perf['total_uses'])
            }

        # Sort by success rate
        sorted_templates = sorted(
            report['performance_summary'].items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )

        report['ranked_templates'] = [
            {
                'rank': i + 1,
                'template': template,
                'success_rate': data['success_rate'],
                'performance_level': data['performance_level']
            }
            for i, (template, data) in enumerate(sorted_templates)
        ]

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Performance report exported to {output_path}")
        return report
