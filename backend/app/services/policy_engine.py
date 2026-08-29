"""
Deterministic Security Policy Gate — T-067, T-068, T-069, T-070.

Evaluates scan findings against configured policy rules to produce PASS/WARNING/BLOCK.
The LLM is NEVER involved in this decision — it may only explain the outcome.
"""

from dataclasses import dataclass, field
from app.core.config import settings
import structlog

logger = structlog.get_logger()


@dataclass
class PolicyConfig:
    """Configurable policy thresholds — T-067."""
    block_on_critical: bool = True
    block_on_exposed_secret: bool = True
    risk_score_warning_threshold: float = 60.0
    risk_score_block_threshold: float = 80.0

    @classmethod
    def from_settings(cls) -> "PolicyConfig":
        return cls(
            block_on_critical=settings.POLICY_BLOCK_ON_CRITICAL,
            block_on_exposed_secret=settings.POLICY_BLOCK_ON_EXPOSED_SECRET,
            risk_score_warning_threshold=settings.POLICY_RISK_SCORE_WARNING_THRESHOLD,
            risk_score_block_threshold=settings.POLICY_RISK_SCORE_BLOCK_THRESHOLD,
        )


@dataclass
class FindingSummary:
    """Summary of a finding's relevant policy attributes."""
    finding_id: str
    severity: str
    tool: str
    risk_score: float | None
    is_true_positive: bool | None


@dataclass
class PolicyResult:
    """Deterministic policy gate result — T-068."""
    gate: str  # "pass" | "warning" | "block"
    triggered_rules: list[str] = field(default_factory=list)
    findings_summary: dict = field(default_factory=dict)


class PolicyEngine:
    """
    T-068: Deterministic PASS/WARNING/BLOCK evaluation.
    All logic is rules-based. The LLM may only explain — not decide — this result.
    """

    def evaluate(
        self,
        findings: list[FindingSummary],
        config: PolicyConfig | None = None,
    ) -> PolicyResult:
        """T-068: Evaluate all findings against policy config."""
        if config is None:
            config = PolicyConfig.from_settings()

        true_positive_findings = [
            f for f in findings
            if f.is_true_positive is not False  # include True and None (unknown)
        ]

        triggered_rules: list[str] = []
        gate = "pass"

        # Rule: BLOCK on critical vulnerability
        critical_findings = [f for f in true_positive_findings if f.severity == "critical"]
        if config.block_on_critical and critical_findings:
            gate = "block"
            triggered_rules.append(
                f"BLOCK: {len(critical_findings)} critical vulnerability(ies) found"
            )

        # Rule: BLOCK on exposed secret (gitleaks findings)
        secret_findings = [
            f for f in true_positive_findings if f.tool == "gitleaks"
        ]
        if config.block_on_exposed_secret and secret_findings:
            gate = "block"
            triggered_rules.append(
                f"BLOCK: {len(secret_findings)} exposed secret(s) detected"
            )

        # Rule: Score-based BLOCK/WARNING
        risk_scores = [
            f.risk_score for f in true_positive_findings
            if f.risk_score is not None
        ]
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            max_risk = max(risk_scores)

            if max_risk >= config.risk_score_block_threshold and gate != "block":
                gate = "block"
                triggered_rules.append(
                    f"BLOCK: Maximum risk score {max_risk:.1f} exceeds block threshold {config.risk_score_block_threshold}"
                )
            elif avg_risk >= config.risk_score_warning_threshold and gate == "pass":
                gate = "warning"
                triggered_rules.append(
                    f"WARNING: Average risk score {avg_risk:.1f} exceeds warning threshold {config.risk_score_warning_threshold}"
                )

        severity_counts = {}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        if not triggered_rules:
            triggered_rules.append("PASS: No critical findings or policy threshold violations")

        result = PolicyResult(
            gate=gate,
            triggered_rules=triggered_rules,
            findings_summary={
                "total": len(findings),
                "true_positives": len(true_positive_findings),
                "by_severity": severity_counts,
            },
        )
        logger.info("Policy gate evaluated", gate=gate, rules=triggered_rules)
        return result


# Singleton instance
policy_engine = PolicyEngine()
