"""
Risk & Validation Agent — Agent 4 (Phase 4) — T-061-T-066.
LLM produces structured risk FACTORS only. Risk score computed by DeterministicRiskEngine.
"""

import json
import structlog
from google import genai
from google.genai import types as genai_types
from app.scanners.semgrep_scanner import NormalizedFinding
from app.services.risk_engine import DeterministicRiskEngine, RiskFactors
from app.core.config import settings

logger = structlog.get_logger()
_risk_engine = DeterministicRiskEngine()


def run_risk_validation_agent(
    finding: NormalizedFinding,
    repo_context: dict,
    security_intelligence: dict,
    historical_status: str | None,
    llm_client: genai.Client,
) -> dict:
    """
    T-061: LLM produces structured risk FACTORS.
    T-063: DeterministicRiskEngine computes final risk_score.
    The LLM MUST NOT output a risk_score — only the six structured factors.
    """
    prompt = f"""You are a security risk analyst. Assess the following vulnerability finding.
Your job is to determine:
1. Whether this is a true positive or likely false positive
2. Structured risk factors (each on a 0-10 scale)

CRITICAL RULE: Do NOT provide a final risk score — only the individual factors.
The risk score is computed separately by a deterministic algorithm, not by you.

## FINDING
Tool: {finding.tool}
Type: {finding.finding_type}
Severity: {finding.severity}
File: {finding.file_path}:{finding.line_start}
Message: {finding.message}
Code: {finding.code_snippet or 'Not available'}

## REPOSITORY CONTEXT
Languages: {repo_context.get('languages', [])}
Frameworks: {repo_context.get('frameworks', [])}
Architecture: {repo_context.get('architecture_summary', 'Not available')}

## SECURITY INTELLIGENCE
{security_intelligence.get('ai_explanation', '')}

## HISTORICAL STATUS
{historical_status or 'First scan — no history available'}

Respond with ONLY this JSON (no markdown, no extra fields):
{{
  "is_true_positive": true or false,
  "exploitability": 0-10,
  "impact": 0-10,
  "confidence": 0-10,
  "exposure": 0-10,
  "business_impact": 0-10,
  "false_positive_rationale": "brief explanation if false positive"
}}

DO NOT include a "risk_score" field."""

    try:
        response = llm_client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=400,
                response_mime_type="application/json",
            ),
        )
        raw = json.loads(response.text)

        # T-066: Enforce that LLM did NOT produce a risk_score
        if "risk_score" in raw:
            logger.warning("LLM produced risk_score — removing to enforce determinism")
            del raw["risk_score"]

        factors = RiskFactors(
            severity_score=_risk_engine.severity_to_score(finding.severity),
            exploitability=float(raw.get("exploitability", 5.0)),
            confidence=float(raw.get("confidence", 5.0)),
            exposure=float(raw.get("exposure", 5.0)),
            business_impact=float(raw.get("business_impact", 5.0)),
        )
        # T-063: Deterministic risk score computation
        risk_score = _risk_engine.compute_score(factors)

        return {
            "is_true_positive": bool(raw.get("is_true_positive", True)),
            "exploitability": factors.exploitability,
            "impact": float(raw.get("impact", 5.0)),
            "confidence": factors.confidence,
            "exposure": factors.exposure,
            "business_impact": factors.business_impact,
            "risk_score": risk_score,  # Set by engine, NOT by LLM
        }

    except Exception as e:
        logger.warning("Risk Validation Agent LLM call failed", error=str(e))
        severity_score = _risk_engine.severity_to_score(finding.severity)
        fallback_factors = RiskFactors(
            severity_score=severity_score,
            exploitability=5.0,
            confidence=5.0,
            exposure=5.0,
            business_impact=5.0,
        )
        return {
            "is_true_positive": True,
            "exploitability": 5.0,
            "impact": 5.0,
            "confidence": 5.0,
            "exposure": 5.0,
            "business_impact": 5.0,
            "risk_score": _risk_engine.compute_score(fallback_factors),
        }
