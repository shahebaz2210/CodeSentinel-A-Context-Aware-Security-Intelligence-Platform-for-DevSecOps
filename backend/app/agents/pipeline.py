"""
LangGraph Orchestrator — Full 5-Agent Pipeline — T-084-T-089.

Wires all 5 agents into a single LangGraph StateGraph:
Repository Analysis → Security Detection → Security Intelligence
→ Risk & Validation → Policy Gate → Remediation
"""

from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
import structlog

logger = structlog.get_logger()


# ── T-086: Shared scan state ──────────────────────────────────────────────────

class ScanState(TypedDict):
    """State object passed between all pipeline nodes."""
    scan_id: str
    repository_id: str
    repo_dir: str
    access_token: str
    clone_url: str
    scan_type: str  # "repo" | "pr"
    pr_changed_files: list[str] | None

    # Agent outputs
    repository_context: dict | None
    findings: list[dict] | None
    finding_analyses: list[dict] | None
    policy_result: dict | None
    remediation_suggestions: list[dict] | None

    # Error state
    error: str | None


def build_scan_pipeline(llm_client: Any) -> Any:
    """
    T-084/T-085: Build and compile the LangGraph pipeline.
    Edges: repo_analysis → security_detection → security_intelligence
           → risk_validation → policy_gate → remediation → END
    """
    from app.agents.repository_analysis_agent import run_repository_analysis_agent
    from app.agents.security_detection_agent import run_security_detection_agent
    from app.agents.security_intelligence_agent import run_security_intelligence_agent
    from app.agents.risk_validation_agent import run_risk_validation_agent
    from app.agents.remediation_agent import run_remediation_agent
    from app.services.policy_engine import policy_engine, FindingSummary

    # ── Node implementations ───────────────────────────────────────────────────

    def node_repo_analysis(state: ScanState) -> dict:
        logger.info("Pipeline: Agent 1 — Repository Analysis", scan_id=state["scan_id"])
        try:
            ctx = run_repository_analysis_agent(
                repo_dir=state["repo_dir"],
                llm_client=llm_client,
                scan_id=state["scan_id"],
            )
            return {"repository_context": ctx}
        except Exception as e:
            logger.error("Agent 1 failed", error=str(e))
            return {"error": f"Repository Analysis failed: {e}"}

    def node_security_detection(state: ScanState) -> dict:
        if state.get("error"):
            return {}
        logger.info("Pipeline: Agent 2 — Security Detection", scan_id=state["scan_id"])
        try:
            normalized = run_security_detection_agent(
                repo_dir=state["repo_dir"],
                pr_changed_files=state.get("pr_changed_files"),
            )
            findings_dicts = [
                {
                    "finding_key": f.finding_key,
                    "tool": f.tool,
                    "finding_type": f.finding_type,
                    "severity": f.severity,
                    "file_path": f.file_path,
                    "line_start": f.line_start,
                    "line_end": f.line_end,
                    "message": f.message,
                    "rule_id": f.rule_id,
                    "code_snippet": f.code_snippet,
                    "raw_output": f.raw_output,
                    "_normalized": f,
                }
                for f in normalized
            ]
            return {"findings": findings_dicts}
        except Exception as e:
            logger.error("Agent 2 failed", error=str(e))
            return {"error": f"Security Detection failed: {e}"}

    def node_security_intelligence(state: ScanState) -> dict:
        if state.get("error"):
            return {}
        logger.info("Pipeline: Agent 3 — Security Intelligence (RAG)", scan_id=state["scan_id"])
        try:
            analyses = []
            for finding_dict in (state.get("findings") or []):
                normalized = finding_dict.get("_normalized")
                if normalized is None:
                    continue
                intel = run_security_intelligence_agent(
                    finding=normalized,
                    repo_context=state.get("repository_context") or {},
                    llm_client=llm_client,
                )
                analyses.append({**finding_dict, **intel})
            return {"finding_analyses": analyses}
        except Exception as e:
            logger.error("Agent 3 failed", error=str(e))
            return {"error": f"Security Intelligence failed: {e}"}

    def node_risk_validation(state: ScanState) -> dict:
        if state.get("error"):
            return {}
        logger.info("Pipeline: Agent 4 — Risk & Validation", scan_id=state["scan_id"])
        try:
            enriched = []
            for item in (state.get("finding_analyses") or []):
                normalized = item.get("_normalized")
                if normalized is None:
                    continue
                risk = run_risk_validation_agent(
                    finding=normalized,
                    repo_context=state.get("repository_context") or {},
                    security_intelligence=item,
                    historical_status=None,  # populated from DB in Celery task
                    llm_client=llm_client,
                )
                enriched.append({**item, **risk})
            return {"finding_analyses": enriched}
        except Exception as e:
            logger.error("Agent 4 failed", error=str(e))
            return {"error": f"Risk Validation failed: {e}"}

    def node_policy_gate(state: ScanState) -> dict:
        if state.get("error"):
            return {}
        logger.info("Pipeline: Policy Gate (deterministic)", scan_id=state["scan_id"])
        try:
            summaries = [
                FindingSummary(
                    finding_id=item.get("finding_key", ""),
                    severity=item.get("severity", "medium"),
                    tool=item.get("tool", ""),
                    risk_score=item.get("risk_score"),
                    is_true_positive=item.get("is_true_positive"),
                )
                for item in (state.get("finding_analyses") or [])
            ]
            result = policy_engine.evaluate(summaries)
            return {
                "policy_result": {
                    "gate": result.gate,
                    "triggered_rules": result.triggered_rules,
                    "findings_summary": result.findings_summary,
                }
            }
        except Exception as e:
            logger.error("Policy Gate failed", error=str(e))
            return {"error": f"Policy Gate failed: {e}"}

    def node_remediation(state: ScanState) -> dict:
        if state.get("error"):
            return {}
        logger.info("Pipeline: Agent 5 — Remediation", scan_id=state["scan_id"])
        try:
            suggestions = []
            for item in (state.get("finding_analyses") or []):
                normalized = item.get("_normalized")
                if normalized is None:
                    continue
                if not item.get("is_true_positive", True):
                    suggestions.append({
                        "finding_key": item["finding_key"],
                        "suggested_fix": None,
                        "validation_status": "not_run",
                        "is_false_positive": True,
                    })
                    continue
                remedy = run_remediation_agent(
                    finding=normalized,
                    risk_analysis=item,
                    security_intelligence=item,
                    llm_client=llm_client,
                )
                suggestions.append({**remedy, "finding_key": item["finding_key"]})
            return {"remediation_suggestions": suggestions}
        except Exception as e:
            logger.error("Agent 5 failed", error=str(e))
            return {"error": f"Remediation failed: {e}"}

    # ── T-084: Build graph ────────────────────────────────────────────────────
    workflow = StateGraph(ScanState)

    workflow.add_node("repo_analysis", node_repo_analysis)
    workflow.add_node("security_detection", node_security_detection)
    workflow.add_node("security_intelligence", node_security_intelligence)
    workflow.add_node("risk_validation", node_risk_validation)
    workflow.add_node("policy_gate", node_policy_gate)
    workflow.add_node("remediation", node_remediation)

    # T-085: Sequential edges
    workflow.set_entry_point("repo_analysis")
    workflow.add_edge("repo_analysis", "security_detection")
    workflow.add_edge("security_detection", "security_intelligence")
    workflow.add_edge("security_intelligence", "risk_validation")
    workflow.add_edge("risk_validation", "policy_gate")
    workflow.add_edge("policy_gate", "remediation")
    workflow.add_edge("remediation", END)

    return workflow.compile()
