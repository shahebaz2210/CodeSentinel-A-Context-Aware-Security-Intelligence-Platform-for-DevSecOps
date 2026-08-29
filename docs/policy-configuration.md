# CodeSentinel — Policy Gate Configuration

The Security Policy Gate evaluates all findings from a scan and assigns one of three gate results:
- **PASS** — No policy violations
- **WARNING** — Issues found that should be addressed but don't block deployment
- **BLOCK** — Critical violations that must be resolved before deployment

> ⚙️ **The policy gate is 100% deterministic** — AI/LLM output is never used to decide the gate result. Only structured, engine-computed values feed into policy evaluation.

---

## Configuration Model

Policy is configured via environment variables or the `PolicyConfig` Pydantic model:

```python
from app.services.policy_engine import PolicyConfig

config = PolicyConfig(
    block_on_critical=True,
    block_on_exposed_secret=True,
    risk_score_warning_threshold=60.0,
    risk_score_block_threshold=80.0,
)
```

---

## Configuration Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `block_on_critical` | `bool` | `True` | Block if **any** finding has severity=`critical` and `is_true_positive=True` |
| `block_on_exposed_secret` | `bool` | `True` | Block if **any** Gitleaks (secret detection) finding is a confirmed true positive |
| `risk_score_warning_threshold` | `float` | `60.0` | Average risk score above this → WARNING |
| `risk_score_block_threshold` | `float` | `80.0` | Average risk score above this → BLOCK |

---

## Policy Evaluation Logic

```
evaluate(findings):
  # Exclude confirmed false positives from all gate decisions
  confirmed = [f for f in findings if f.is_true_positive != False]

  if block_on_critical and any(f.severity == "critical" for f in confirmed):
    return BLOCK (triggered_rule: "critical_finding")

  if block_on_exposed_secret and any(f.tool == "gitleaks" for f in confirmed):
    return BLOCK (triggered_rule: "exposed_secret")

  avg_risk = mean(f.risk_score for f in confirmed if f.risk_score is not None)

  if avg_risk >= risk_score_block_threshold:
    return BLOCK (triggered_rule: "high_avg_risk_score")

  if avg_risk >= risk_score_warning_threshold:
    return WARNING (triggered_rule: "elevated_avg_risk_score")

  return PASS
```

---

## Tuning Guidance

### Making the gate stricter
- Lower `risk_score_warning_threshold` (e.g., 40.0) to warn on more findings
- Lower `risk_score_block_threshold` (e.g., 65.0) to block more aggressively

### Making the gate more permissive
- Set `block_on_critical=False` to allow critical findings without blocking
- Raise `risk_score_block_threshold` (e.g., 90.0) to only block on very high risk

### PR vs Repository scans
Currently the same `PolicyConfig` applies to both scan types. A future enhancement will allow separate configurations per scan type.

---

## Risk Score Computation

Risk scores (0–100) are computed by `DeterministicRiskEngine`:

```
risk_score = (
    severity_weight    × severity_score      +
    exploitability_w   × exploitability      +
    confidence_w       × confidence          +
    exposure_w         × exposure            +
    business_impact_w  × business_impact
) × 10  # normalized to 0–100
```

Default weights:

| Factor | Weight |
|---|---|
| Severity | 0.35 |
| Exploitability | 0.25 |
| Confidence | 0.15 |
| Exposure | 0.15 |
| Business Impact | 0.10 |

Weights **must sum to 1.0** — this is enforced at engine initialization and tested in CI.

---

## Environment Variable Overrides

```dotenv
POLICY_BLOCK_ON_CRITICAL=true
POLICY_BLOCK_ON_SECRET=true
POLICY_WARNING_THRESHOLD=60.0
POLICY_BLOCK_THRESHOLD=80.0
RISK_WEIGHT_SEVERITY=0.35
RISK_WEIGHT_EXPLOITABILITY=0.25
RISK_WEIGHT_CONFIDENCE=0.15
RISK_WEIGHT_EXPOSURE=0.15
RISK_WEIGHT_BUSINESS_IMPACT=0.10
```
