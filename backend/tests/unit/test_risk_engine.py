"""Unit tests for the Deterministic Risk Engine — T-019, T-064."""

import pytest
from app.services.risk_engine import DeterministicRiskEngine, RiskFactors


@pytest.fixture
def engine() -> DeterministicRiskEngine:
    return DeterministicRiskEngine()


def test_risk_engine_weights_sum_to_one(engine: DeterministicRiskEngine) -> None:
    """T-064: Risk engine weights must sum to 1.0 (enforced in constructor)."""
    total = (
        engine.weight_severity
        + engine.weight_exploitability
        + engine.weight_confidence
        + engine.weight_exposure
        + engine.weight_business_impact
    )
    assert abs(total - 1.0) < 1e-9


def test_risk_engine_critical_high_score(engine: DeterministicRiskEngine) -> None:
    """Critical finding with high risk factors should produce high risk score."""
    factors = RiskFactors(
        severity_score=10.0,
        exploitability=9.0,
        confidence=9.0,
        exposure=8.0,
        business_impact=9.0,
    )
    score = engine.compute_score(factors)
    assert score >= 80.0, f"Expected high score for critical finding, got {score}"


def test_risk_engine_low_finding_low_score(engine: DeterministicRiskEngine) -> None:
    """Low severity finding with low risk factors should produce low risk score."""
    factors = RiskFactors(
        severity_score=2.5,
        exploitability=2.0,
        confidence=2.0,
        exposure=1.0,
        business_impact=1.5,
    )
    score = engine.compute_score(factors)
    assert score <= 40.0, f"Expected low score for low finding, got {score}"


def test_risk_engine_output_always_in_0_100(engine: DeterministicRiskEngine) -> None:
    """Risk score must always be in [0, 100] — no matter the inputs."""
    for severity_score in [0.0, 10.0]:
        for other in [0.0, 10.0]:
            factors = RiskFactors(
                severity_score=severity_score,
                exploitability=other,
                confidence=other,
                exposure=other,
                business_impact=other,
            )
            score = engine.compute_score(factors)
            assert 0.0 <= score <= 100.0


def test_severity_mapping(engine: DeterministicRiskEngine) -> None:
    """Severity string to score mapping should produce correct values."""
    assert engine.severity_to_score("critical") == 10.0
    assert engine.severity_to_score("high") == 7.5
    assert engine.severity_to_score("medium") == 5.0
    assert engine.severity_to_score("low") == 2.5
    assert engine.severity_to_score("info") == 1.0
    # Unknown defaults to medium
    assert engine.severity_to_score("unknown") == 5.0
