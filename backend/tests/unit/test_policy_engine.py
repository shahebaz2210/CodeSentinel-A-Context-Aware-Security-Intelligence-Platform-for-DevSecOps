"""Unit tests for the Policy Engine (deterministic gate) — T-019."""

import pytest
from app.services.policy_engine import PolicyEngine, PolicyConfig, FindingSummary


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
def strict_config() -> PolicyConfig:
    return PolicyConfig(
        block_on_critical=True,
        block_on_exposed_secret=True,
        risk_score_warning_threshold=60.0,
        risk_score_block_threshold=80.0,
    )


def test_policy_engine_pass_with_no_findings(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """Empty findings list should produce PASS gate."""
    result = engine.evaluate([], config=strict_config)
    assert result.gate == "pass"


def test_policy_engine_block_on_critical(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """A single critical finding should trigger BLOCK gate."""
    findings = [
        FindingSummary("f1", severity="critical", tool="semgrep", risk_score=85.0, is_true_positive=True)
    ]
    result = engine.evaluate(findings, config=strict_config)
    assert result.gate == "block"
    assert any("critical" in rule.lower() for rule in result.triggered_rules)


def test_policy_engine_block_on_secret(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """A gitleaks finding should trigger BLOCK regardless of severity set."""
    findings = [
        FindingSummary("f2", severity="high", tool="gitleaks", risk_score=70.0, is_true_positive=True)
    ]
    result = engine.evaluate(findings, config=strict_config)
    assert result.gate == "block"


def test_policy_engine_warning_on_high_avg_risk(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """Average risk score above warning threshold should produce WARNING."""
    findings = [
        FindingSummary("f3", severity="high", tool="semgrep", risk_score=65.0, is_true_positive=True),
        FindingSummary("f4", severity="medium", tool="semgrep", risk_score=62.0, is_true_positive=True),
    ]
    result = engine.evaluate(findings, config=strict_config)
    assert result.gate == "warning"


def test_policy_engine_false_positive_excluded(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """False positive findings should not trigger policy gate."""
    findings = [
        FindingSummary("f5", severity="critical", tool="semgrep", risk_score=90.0, is_true_positive=False)
    ]
    result = engine.evaluate(findings, config=strict_config)
    # False positives are excluded from gate evaluation
    assert result.gate == "pass"


def test_policy_engine_findings_summary_populated(engine: PolicyEngine, strict_config: PolicyConfig) -> None:
    """Policy result should include findings summary with counts."""
    findings = [
        FindingSummary("f6", severity="high", tool="semgrep", risk_score=50.0, is_true_positive=True),
        FindingSummary("f7", severity="medium", tool="trivy", risk_score=30.0, is_true_positive=True),
    ]
    result = engine.evaluate(findings, config=strict_config)
    assert result.findings_summary["total"] == 2
    assert result.findings_summary["by_severity"]["high"] == 1
