"""
Security Intelligence Agent — Agent 3 (Phase 3) — T-056-T-060.
RAG-grounded LLM explanations for each finding.
All explanations MUST be grounded in retrieved OWASP/CWE documents.
"""

import json
import structlog
from google import genai                    # new SDK — used for runtime
from google.genai import types as genai_types
import google.generativeai as _old_genai   # kept only for type hints
from app.scanners.semgrep_scanner import NormalizedFinding
from app.services.rag_service import search_knowledge
from app.core.config import settings

logger = structlog.get_logger()


def finding_to_query(finding: NormalizedFinding) -> str:
    """T-056: Convert a finding to a descriptive query for vector search."""
    return (
        f"{finding.finding_type.replace('_', ' ').lower()} vulnerability "
        f"in {finding.tool} scan: {finding.message[:200]}"
    )


def run_security_intelligence_agent(
    finding: NormalizedFinding,
    repo_context: dict,
    llm_client: genai.Client,
) -> dict:
    """
    T-057: For each finding, retrieve RAG context and generate grounded explanation.
    The LLM explanation MUST be grounded in retrieved documents — never pure model memory.
    """
    # T-057a: Vector search for relevant security knowledge
    query = finding_to_query(finding)
    relevant_docs = search_knowledge(query, top_k=settings.RAG_TOP_K)

    # Format retrieved documents for the LLM prompt
    rag_context = "\n\n---\n\n".join(
        f"Source: {doc['source']} (score: {doc['score']:.2f})\n{doc['text'][:800]}"
        for doc in relevant_docs
    )

    owasp_refs = [doc["owasp_id"] for doc in relevant_docs if doc.get("owasp_id")]
    cwe_refs = [doc["cwe_id"] for doc in relevant_docs if doc.get("cwe_id")]

    # T-058: Prompt explicitly instructs LLM to ground in retrieved documents
    prompt = f"""You are a security expert analyzing a vulnerability finding.
You MUST base your analysis on the security knowledge documents provided below.
Do NOT invent information not supported by the retrieved documents or the finding details.

## FINDING DETAILS
Tool: {finding.tool}
Type: {finding.finding_type}
Severity: {finding.severity}
File: {finding.file_path}:{finding.line_start}
Message: {finding.message}
Code snippet: {finding.code_snippet or 'Not available'}

## REPOSITORY CONTEXT
Languages: {repo_context.get('languages', [])}
Frameworks: {repo_context.get('frameworks', [])}

## RETRIEVED SECURITY KNOWLEDGE (OWASP/CWE/Secure Coding Guidance)
{rag_context if rag_context else 'No relevant documents retrieved.'}

## INSTRUCTIONS
Based ONLY on the above, provide a JSON response with these exact fields:
{{
  "vulnerability_explanation": "Clear explanation of what this vulnerability is",
  "root_cause": "Root cause of this specific finding",
  "impact": "Potential security impact",
  "attack_scenario": "How an attacker could exploit this",
  "security_recommendations": "Specific recommendations to fix this",
  "owasp_references": ["list of OWASP categories if mentioned in retrieved docs"],
  "cwe_references": ["list of CWE IDs if mentioned in retrieved docs"]
}}

Respond with ONLY the JSON object, no markdown wrapping."""

    try:
        response = llm_client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=1000,
                response_mime_type="application/json",
            ),
        )
        result = json.loads(response.text)
    except Exception as e:
        logger.warning("Security Intelligence Agent LLM call failed", error=str(e))
        result = {
            "vulnerability_explanation": f"Scanner detected: {finding.message}",
            "root_cause": "Analysis unavailable",
            "impact": "Unknown — manual review required",
            "attack_scenario": "Unknown",
            "security_recommendations": "Review and fix the flagged code",
            "owasp_references": [],
            "cwe_references": [],
        }

    # Merge extracted refs with those from retrieved docs
    all_owasp = list(set(owasp_refs + result.get("owasp_references", [])))
    all_cwe = list(set(cwe_refs + result.get("cwe_references", [])))

    return {
        "ai_explanation": result.get("vulnerability_explanation", ""),
        "root_cause": result.get("root_cause", ""),
        "attack_scenario": result.get("attack_scenario", ""),
        "security_recommendations": result.get("security_recommendations", ""),
        "owasp_refs": all_owasp,
        "cwe_refs": all_cwe,
    }
