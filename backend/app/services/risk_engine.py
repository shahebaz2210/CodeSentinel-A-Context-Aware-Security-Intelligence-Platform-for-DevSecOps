"""
Deterministic Risk Engine — T-063, T-065.

Computes the final numerical risk score from structured risk factors.
The LLM NEVER produces this score — it only produces the input risk factors.
This separation makes risk scoring reproducible, auditable, and explainable.
"""

from dataclasses import dataclass
from app.core.config import settings


@dataclass
class RiskFactors:
    """Structured risk factors produced by the LLM (Agent 4). Not the final score."""
    severity_score: float  # 0-10, mapped from finding severity
    exploitability: float  # 0-10, LLM-assessed
    confidence: float      # 0-10, LLM-assessed
    exposure: float        # 0-10, LLM-assessed
    business_impact: float # 0-10, LLM-assessed


SEVERITY_TO_SCORE = {
    "critical": 10.0,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 1.0,
}


class DeterministicRiskEngine:
    """
    Computes final risk scores using a fixed, configurable weighted formula.
    Weights are defined in settings — not chosen by the LLM.
    Output is always in [0.0, 100.0].
    """

    def __init__(self) -> None:
        self.weight_severity = settings.RISK_WEIGHT_SEVERITY
        self.weight_exploitability = settings.RISK_WEIGHT_EXPLOITABILITY
        self.weight_confidence = settings.RISK_WEIGHT_CONFIDENCE
        self.weight_exposure = settings.RISK_WEIGHT_EXPOSURE
        self.weight_business_impact = settings.RISK_WEIGHT_BUSINESS_IMPACT

        # Validate weights sum to 1.0
        total = (
            self.weight_severity
            + self.weight_exploitability
            + self.weight_confidence
            + self.weight_exposure
            + self.weight_business_impact
        )
        assert abs(total - 1.0) < 1e-9, f"Risk weights must sum to 1.0, got {total}"

    def compute_score(self, factors: RiskFactors) -> float:
        """
        T-063: Compute the final risk score deterministically.
        Returns a float in [0.0, 100.0].
        """
        # Normalize all factors to 0-10 scale, then weight
        raw = (
            self.weight_severity * factors.severity_score
            + self.weight_exploitability * factors.exploitability
            + self.weight_confidence * factors.confidence
            + self.weight_exposure * factors.exposure
            + self.weight_business_impact * factors.business_impact
        )
        # Scale to 0-100 and clamp
        score = (raw / 10.0) * 100.0
        return max(0.0, min(100.0, round(score, 2)))

    @staticmethod
    def severity_to_score(severity: str) -> float:
        """Map a severity label to a numeric 0-10 score."""
        return SEVERITY_TO_SCORE.get(severity.lower(), 5.0)


# Singleton instance
risk_engine = DeterministicRiskEngine()
