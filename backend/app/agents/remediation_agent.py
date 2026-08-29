"""
Remediation Agent — Agent 5 (Phase 5) — T-071-T-074.
Generates context-aware remediation guidance.
All output is framed as a suggestion pending validation — never as a final trusted fix.
"""

import json
import structlog
from google import genai
from google.genai import types as genai_types
from app.scanners.semgrep_scanner import NormalizedFinding
from app.core.config import settings

logger = structlog.get_logger()


def run_remediation_agent(
    finding: NormalizedFinding,
    risk_analysis: dict,
    security_intelligence: dict,
    llm_client: genai.Client,
) -> dict:
    """
    T-071: Generate remediation guidance grounded in the finding and security knowledge.
    T-072: Output must be framed as a suggestion — never as ready-to-apply or safe without validation.
    """
    prompt = f"""You are a secure coding expert providing remediation guidance.
Generate a concrete, specific fix for the security vulnerability below.

IMPORTANT: Your suggested fix is a SUGGESTION that must pass automated validation
(tests + re-scan) before being trusted. Do not imply it is safe without validation.

## VULNERABILITY
Type: {finding.finding_type}
Severity: {finding.severity}
File: {finding.file_path}
Message: {finding.message}

## VULNERABLE CODE
```
{finding.code_snippet or 'Not available — see file above'}
```

## SECURITY CONTEXT
Explanation: {security_intelligence.get('ai_explanation', '')}
OWASP: {', '.join(security_intelligence.get('owasp_refs', []))}
CWE: {', '.join(security_intelligence.get('cwe_refs', []))}

## RISK
Score: {risk_analysis.get('risk_score', 'Unknown')}/100
Is confirmed vulnerability: {risk_analysis.get('is_true_positive', True)}

Respond with ONLY this JSON:
{{
  "fix_explanation": "Why the fix resolves the vulnerability",
  "suggested_fix": "The corrected code snippet or diff showing what to change",
  "secure_coding_guidance": "General secure coding principles to apply",
  "additional_notes": "Any caveats or additional steps needed"
}}"""

    try:
        response = llm_client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=800,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
    except Exception as e:
        logger.warning("Remediation Agent LLM call failed", error=str(e))
        result = {
            "fix_explanation": "Manual remediation required",
            "suggested_fix": "Review and fix the flagged code",
            "secure_coding_guidance": "Apply secure coding best practices for this vulnerability type",
            "additional_notes": "",
        }

    return {
        "suggested_fix": result.get("suggested_fix", ""),
        "secure_coding_guidance": result.get("secure_coding_guidance", ""),
        "fix_explanation": result.get("fix_explanation", ""),
        # validation_status is set to "not_run" by default in the model
    }
