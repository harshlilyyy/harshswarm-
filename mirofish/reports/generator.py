# =============================================================================
# REPORT GENERATOR — Comprehensive Analysis Output
# =============================================================================
"""
Generates comprehensive reports from simulation results:
- Executive summaries
- Key actor trajectories
- Major turning points
- Predicted outcomes with confidence estimates
- Risk assessments
- Alternative scenarios
- Source citations from simulation traces
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import json


@dataclass
class ReportSection:
    """A section of the generated report."""
    title: str
    content: str
    subsections: List['ReportSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "subsections": [s.to_dict() for s in self.subsections],
            "metadata": self.metadata
        }
    
    def to_markdown(self, level: int = 2) -> str:
        """Convert section to Markdown format."""
        heading = "#" * level
        md = f"{heading} {self.title}\n\n{self.content}\n"
        
        for subsection in self.subsections:
            md += "\n" + subsection.to_markdown(level + 1)
        
        return md


@dataclass
class ExecutiveSummary:
    """Executive summary of simulation results."""
    overview: str
    key_findings: List[str]
    confidence_level: str
    recommended_actions: List[str]
    risk_level: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overview": self.overview,
            "key_findings": self.key_findings,
            "confidence_level": self.confidence_level,
            "recommended_actions": self.recommended_actions,
            "risk_level": self.risk_level
        }


class ReportGenerator:
    """
    Generates comprehensive reports from simulation and prediction results.
    
    Features:
    - Multiple output formats (dict, markdown, JSON)
    - Configurable detail levels
    - Citation tracking
    - Visual element suggestions
    """
    
    def __init__(self, include_citations: bool = True,
                 detail_level: str = "full"):
        """
        Initialize report generator.
        
        Args:
            include_citations: Whether to include source citations
            detail_level: "brief", "standard", or "full"
        """
        self.include_citations = include_citations
        self.detail_level = detail_level
    
    def generate(self, prediction_result: Any,
                 simulation_results: Optional[List[Any]] = None,
                 custom_sections: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report.
        
        Args:
            prediction_result: PredictionResult from Monte Carlo sampling
            simulation_results: Optional list of individual simulation results
            custom_sections: Optional custom sections to include
        
        Returns:
            Complete report as dictionary
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_type": "swarm_intelligence_prediction",
            "executive_summary": self._generate_executive_summary(prediction_result),
            "prediction_overview": self._generate_prediction_overview(prediction_result),
            "scenario_analysis": self._generate_scenario_analysis(prediction_result),
            "risk_assessment": self._generate_risk_assessment(prediction_result),
            "actor_trajectories": self._generate_actor_trajectories(prediction_result),
            "turning_points": self._generate_turning_points(prediction_result),
            "alternative_scenarios": self._generate_alternatives(prediction_result),
            "methodology": self._generate_methodology(prediction_result),
        }
        
        if self.include_citations:
            report["citations"] = self._generate_citations(prediction_result, simulation_results)
        
        if custom_sections:
            for section in custom_sections:
                report[section.get('title', 'Custom Section')] = section.get('content', '')
        
        return report
    
    def _generate_executive_summary(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate executive summary section."""
        most_likely = prediction_result.most_likely_scenario
        uncertainty = prediction_result.uncertainty_metrics
        
        # Determine confidence level
        confidence = uncertainty.get('prediction_confidence', 0.5)
        if confidence > 0.8:
            confidence_level = "High"
        elif confidence > 0.6:
            confidence_level = "Moderate"
        else:
            confidence_level = "Low"
        
        # Determine risk level
        cascade_dist = prediction_result.outcome_distribution.get('cascade_rate', {})
        mean_cascade = cascade_dist.get('mean', 0)
        
        if mean_cascade > 0.3:
            risk_level = "High"
        elif mean_cascade > 0.15:
            risk_level = "Moderate"
        else:
            risk_level = "Low"
        
        # Generate overview
        mode = most_likely.get('dominant_mode', 'UNKNOWN')
        probability = most_likely.get('probability', 0)
        description = most_likely.get('description', '')
        
        overview = (
            f"Based on {len(prediction_result.samples)} parallel world simulations, "
            f"the most likely outcome ({probability*100:.1f}% probability) is characterized by "
            f"{mode} behavior patterns across the agent population. {description} "
            f"The prediction carries {confidence_level.lower()} confidence "
            f"(confidence score: {confidence:.2f})."
        )
        
        # Key findings
        key_findings = [
            f"Dominant behavioral mode: {mode}",
            f"Mean cascade rate: {mean_cascade*100:.1f}%",
            f"Prediction confidence: {confidence*100:.1f}%",
            f"Scenario entropy: {uncertainty.get('scenario_entropy', 0):.2f}"
        ]
        
        # Recommended actions based on scenario
        recommended_actions = self._get_recommendations(mode, risk_level)
        
        return {
            "overview": overview,
            "key_findings": key_findings,
            "confidence_level": confidence_level,
            "recommended_actions": recommended_actions,
            "risk_level": risk_level
        }
    
    def _get_recommendations(self, mode: str, risk_level: str) -> List[str]:
        """Generate recommendations based on predicted scenario."""
        recommendations = []
        
        if mode == "RECOVER" or risk_level == "High":
            recommendations.extend([
                "Implement support systems to prevent cascade failures",
                "Increase mentorship and social support programs",
                "Monitor vulnerable populations closely"
            ])
        elif mode == "AVOID":
            recommendations.extend([
                "Reduce environmental stressors where possible",
                "Create low-pressure engagement opportunities",
                "Build confidence through incremental successes"
            ])
        elif mode == "EXECUTE":
            recommendations.extend([
                "Channel high energy into productive initiatives",
                "Ensure adequate resources to sustain momentum",
                "Monitor for burnout risks"
            ])
        else:
            recommendations.append("Maintain current supportive conditions")
        
        return recommendations
    
    def _generate_prediction_overview(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate detailed prediction overview."""
        dist = prediction_result.outcome_distribution
        
        return {
            "cascade_rate_statistics": dist.get('cascade_rate', {}),
            "anxiety_statistics": dist.get('anxiety', {}),
            "self_worth_statistics": dist.get('self_worth', {}),
            "mode_distribution": dist.get('dominant_modes', {}),
            "confidence_intervals": prediction_result.confidence_intervals,
            "sample_size": len(prediction_result.samples)
        }
    
    def _generate_scenario_analysis(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate scenario analysis section."""
        most_likely = prediction_result.most_likely_scenario
        
        return {
            "primary_scenario": {
                "mode": most_likely.get('dominant_mode'),
                "probability": most_likely.get('probability'),
                "description": most_likely.get('description'),
                "implications": self._get_implications(most_likely.get('dominant_mode'))
            },
            "stability_analysis": {
                "mean_stability": sum(s.outcome.get('stability_score', 0) for s in prediction_result.samples) / len(prediction_result.samples) if prediction_result.samples else 0,
                "factors_affecting_stability": [
                    "Success/failure event distribution",
                    "Social network cohesion",
                    "Resource availability"
                ]
            }
        }
    
    def _get_implications(self, mode: str) -> List[str]:
        """Get implications for a given scenario mode."""
        implications = {
            "EXECUTE": [
                "High productivity expected",
                "Risk of overextension",
                "Opportunity for significant progress"
            ],
            "OPTIMIZE": [
                "Steady, sustainable progress",
                "Lower volatility",
                "Incremental improvements accumulate"
            ],
            "AVOID": [
                "Reduced engagement and participation",
                "Potential for missed opportunities",
                "Need for intervention to reverse trajectory"
            ],
            "RECOVER": [
                "System under stress",
                "Support interventions critical",
                "Recovery time required"
            ],
            "SPIKE": [
                "High output but unsustainable",
                "Burnout risk elevated",
                "Channel energy carefully"
            ]
        }
        return implications.get(mode, ["Uncertain implications"])
    
    def _generate_risk_assessment(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate risk assessment section."""
        uncertainty = prediction_result.uncertainty_metrics
        dist = prediction_result.outcome_distribution
        
        cascade_dist = dist.get('cascade_rate', {})
        
        return {
            "overall_risk_level": self._calculate_risk_level(cascade_dist),
            "cascade_risk": {
                "mean_rate": cascade_dist.get('mean', 0),
                "worst_case": cascade_dist.get('max', 0),
                "uncertainty": cascade_dist.get('std', 0)
            },
            "vulnerability_factors": [
                "High anxiety variance indicates polarization",
                "Cascade failures can spread through social networks",
                "External shocks may trigger tipping points"
            ],
            "mitigation_strategies": [
                "Strengthen social support networks",
                "Reduce systemic stressors",
                "Build resilience through skill development",
                "Create early warning systems"
            ],
            "uncertainty_assessment": {
                "prediction_confidence": uncertainty.get('prediction_confidence', 0),
                "scenario_entropy": uncertainty.get('scenario_entropy', 0),
                "interpretation": self._interpret_uncertainty(uncertainty)
            }
        }
    
    def _calculate_risk_level(self, cascade_dist: Dict) -> str:
        """Calculate overall risk level."""
        mean = cascade_dist.get('mean', 0)
        worst = cascade_dist.get('max', 0)
        
        if worst > 0.5 or mean > 0.3:
            return "HIGH"
        elif worst > 0.3 or mean > 0.15:
            return "MODERATE"
        else:
            return "LOW"
    
    def _interpret_uncertainty(self, uncertainty: Dict) -> str:
        """Interpret uncertainty metrics."""
        confidence = uncertainty.get('prediction_confidence', 0.5)
        entropy = uncertainty.get('scenario_entropy', 0)
        
        if confidence > 0.8 and entropy < 1.0:
            return "Predictions are relatively reliable; primary scenario is well-defined"
        elif confidence > 0.6:
            return "Moderate reliability; consider multiple scenarios in planning"
        else:
            return "High uncertainty; predictions should be treated as exploratory rather than definitive"
    
    def _generate_actor_trajectories(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate actor trajectory analysis."""
        # Aggregate trajectory data from samples
        all_trajectories = []
        for sample in prediction_result.samples[:10]:  # Sample of trajectories
            all_trajectories.extend(sample.trajectory)
        
        if not all_trajectories:
            return {"trajectories": [], "patterns": []}
        
        # Analyze patterns
        avg_anxiety_trend = self._analyze_trend(
            [t.get('avg_anxiety', 0.5) for t in all_trajectories]
        )
        
        return {
            "sample_size": len(all_trajectories),
            "average_trajectory_patterns": {
                "anxiety_trend": avg_anxiety_trend,
                "typical_mode_transitions": self._get_typical_transitions()
            },
            "notable_patterns": [
                "Initial anxiety often decreases with successful interactions",
                "Cascade events typically cluster in time",
                "Recovery trajectories show gradual improvement"
            ]
        }
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend in values."""
        if len(values) < 2:
            return "insufficient data"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if abs(diff) < 0.05:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _get_typical_transitions(self) -> List[str]:
        """Get typical mode transition patterns."""
        return [
            "OPTIMIZE → EXECUTE (success builds momentum)",
            "EXECUTE → AVOID (failure triggers withdrawal)",
            "AVOID → RECOVER (continued failure leads to cascade)",
            "RECOVER → OPTIMIZE (support enables recovery)"
        ]
    
    def _generate_turning_points(self, prediction_result: Any) -> Dict[str, Any]:
        """Identify major turning points from causal chains."""
        all_events = []
        for sample in prediction_result.samples:
            all_events.extend(sample.causal_chain)
        
        # Count event types
        success_count = sum(1 for e in all_events if e.get('effect') == 'success')
        failure_count = sum(1 for e in all_events if e.get('effect') == 'failure')
        
        return {
            "total_significant_events": len(all_events),
            "success_events": success_count,
            "failure_events": failure_count,
            "success_ratio": success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0,
            "critical_thresholds": [
                "3+ consecutive failures often trigger cascade",
                "Sustained success (>5 events) builds resilient momentum",
                "Mentorship events can interrupt negative cascades"
            ]
        }
    
    def _generate_alternatives(self, prediction_result: Any) -> Dict[str, Any]:
        """Generate alternative scenarios section."""
        alternatives = prediction_result.alternative_scenarios
        
        return {
            "scenarios": [
                {
                    "name": alt.get('scenario'),
                    "probability": alt.get('probability'),
                    "description": alt.get('description'),
                    "cascade_rate": alt.get('avg_cascade_rate')
                }
                for alt in alternatives
            ],
            "comparison_factors": [
                "Behavioral mode distribution",
                "Cascade failure rates",
                "Population anxiety levels",
                "System stability"
            ]
        }
    
    def _generate_methodology(self, prediction_result: Any) -> Dict[str, Any]:
        """Document methodology used."""
        metadata = prediction_result.metadata
        
        return {
            "sampling_method": "Monte Carlo simulation",
            "num_samples": metadata.get('total_samples', len(prediction_result.samples)),
            "seeds_used": metadata.get('seeds_used', [])[:5],
            "model_components": [
                "Cognitive agents with Big Five personality traits",
                "Schwartz value orientations",
                "Multi-component memory system",
                "Dynamic psychological state machine",
                "Social influence networks"
            ],
            "limitations": [
                "Model simplifies complex human psychology",
                "Results are probabilistic, not deterministic",
                "External factors not modeled may affect outcomes"
            ]
        }
    
    def _generate_citations(self, prediction_result: Any,
                           simulation_results: Optional[List]) -> List[Dict]:
        """Generate citations from simulation traces."""
        citations = []
        
        # Add seed citations
        for i, seed in enumerate(prediction_result.metadata.get('seeds_used', [])[:5]):
            citations.append({
                "type": "simulation_seed",
                "id": f"sample_{i}",
                "seed": seed,
                "description": f"Monte Carlo sample {i}"
            })
        
        # Add metric citations
        if prediction_result.metrics_history if hasattr(prediction_result, 'metrics_history') else []:
            citations.append({
                "type": "metrics_collection",
                "source": "aggregated_simulation_metrics",
                "description": "Time-series metrics from simulation runs"
            })
        
        return citations
    
    def to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report dictionary to Markdown format."""
        md = "# MiroFish Prediction Report\n\n"
        md += f"*Generated: {report.get('generated_at', 'Unknown')}*\n\n"
        
        # Executive Summary
        summary = report.get('executive_summary', {})
        md += "## Executive Summary\n\n"
        md += f"{summary.get('overview', '')}\n\n"
        
        md += "### Key Findings\n"
        for finding in summary.get('key_findings', []):
            md += f"- {finding}\n"
        
        md += f"\n**Confidence Level:** {summary.get('confidence_level', 'Unknown')}\n"
        md += f"**Risk Level:** {summary.get('risk_level', 'Unknown')}\n\n"
        
        # Scenario Analysis
        scenario = report.get('scenario_analysis', {})
        md += "## Scenario Analysis\n\n"
        primary = scenario.get('primary_scenario', {})
        md += f"### Primary Scenario: {primary.get('mode', 'Unknown')}\n\n"
        md += f"{primary.get('description', '')}\n\n"
        
        # Risk Assessment
        risk = report.get('risk_assessment', {})
        md += "## Risk Assessment\n\n"
        md += f"**Overall Risk:** {risk.get('overall_risk_level', 'Unknown')}\n\n"
        
        # Citations
        if report.get('citations'):
            md += "## Citations\n\n"
            for citation in report['citations']:
                md += f"- [{citation.get('type')}] {citation.get('description')}\n"
        
        return md
    
    def to_json(self, report: Dict[str, Any], indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(report, indent=indent, default=str)
