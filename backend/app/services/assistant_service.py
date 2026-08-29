"""
AI Security Assistant Service — T-115, T-116, T-118.
Answers developer questions grounded in real scan data + RAG.
"""

import uuid
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from google import genai
from google.genai import types as genai_types

from app.core.config import settings
from app.models import Scan, Finding, Repository
from app.models.scan import ScanStatus
from app.services.rag_service import search_knowledge
import structlog

logger = structlog.get_logger()


class AssistantService:
    """T-115: Grounds every assistant answer in real findings + RAG knowledge."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def _retrieve_scan_context(self, scan_id: str | None, finding_id: str | None) -> dict:
        """Retrieve current findings, scan summary, and historical data from PostgreSQL."""
        context = {
            "findings": [],
            "scan_summary": None,
            "repo_name": None,
            "historical_note": None,
        }

        if scan_id:
            scan = self.db.query(Scan).filter(Scan.id == uuid.UUID(scan_id)).first()
            if scan:
                repo = scan.repository
                context["scan_summary"] = {
                    "scan_id": scan_id,
                    "score": float(scan.security_score) if scan.security_score else None,
                    "gate": scan.gate_result.value if scan.gate_result else None,
                    "type": scan.scan_type.value,
                }
                context["repo_name"] = repo.full_name if repo else None
                context["findings"] = [
                    {
                        "id": str(f.id),
                        "type": f.finding_type,
                        "severity": f.severity.value,
                        "file": f.file_path,
                        "line": f.line_start,
                        "risk_score": float(f.analysis.risk_score) if f.analysis and f.analysis.risk_score else None,
                        "owasp": f.analysis.owasp_refs if f.analysis else [],
                        "cwe": f.analysis.cwe_refs if f.analysis else [],
                        "history": f.history[0].history_status.value if f.history else "unknown",
                    }
                    for f in scan.findings
                ][:20]  # cap at 20 findings for context window

                # Historical context
                if repo:
                    prev_scans = (
                        self.db.query(Scan)
                        .filter(
                            Scan.repository_id == repo.id,
                            Scan.status == ScanStatus.COMPLETED,
                            Scan.id != scan.id,
                        )
                        .order_by(Scan.created_at.desc())
                        .limit(3)
                        .all()
                    )
                    if prev_scans:
                        scores = [float(s.security_score) for s in prev_scans if s.security_score]
                        context["historical_note"] = (
                            f"Previous {len(prev_scans)} scan(s) had scores: {scores}"
                        )

        if finding_id:
            finding = self.db.query(Finding).filter(Finding.id == uuid.UUID(finding_id)).first()
            if finding and not any(f["id"] == finding_id for f in context["findings"]):
                context["findings"].insert(0, {
                    "id": finding_id,
                    "type": finding.finding_type,
                    "severity": finding.severity.value,
                    "file": finding.file_path,
                    "risk_score": float(finding.analysis.risk_score) if finding.analysis and finding.analysis.risk_score else None,
                })

        return context

    async def stream_answer(
        self,
        question: str,
        scan_id: str | None,
        finding_id: str | None,
    ) -> AsyncGenerator[str, None]:
        """
        T-117: Stream a RAG-grounded answer to the developer's question.
        T-116: Answer MUST be grounded in retrieved data, not model memory alone.
        """
        # Retrieve from PostgreSQL
        scan_context = self._retrieve_scan_context(scan_id, finding_id)

        # T-116: Retrieve RAG context
        rag_docs = search_knowledge(question, top_k=3)
        rag_text = "\n\n".join(
            f"[{doc['source']}]: {doc['text'][:600]}"
            for doc in rag_docs
        )

        findings_text = "\n".join(
            f"- Finding {f['id']}: {f['type']} [{f['severity'].upper()}] "
            f"in {f['file']} (risk: {f.get('risk_score', 'N/A')}, history: {f.get('history', 'N/A')})"
            for f in scan_context["findings"]
        ) or "No findings loaded."

        # T-116: System prompt enforces grounding rule
        system_prompt = f"""You are the CodeSentinel AI Security Assistant.
You help developers understand security vulnerabilities found in their code.

CRITICAL RULES:
1. Base your answers on the ACTUAL FINDINGS and SCAN DATA provided below — not general knowledge alone.
2. When referencing a finding, cite its ID (e.g., "Finding F-1024").
3. Never invent findings that are not in the provided data.
4. CodeSentinel does NOT approve or merge pull requests — always clarify this if asked.
5. Risk scores and gate results are computed deterministically — always attribute them to "the security analysis engine", not "the AI".

## CURRENT SCAN DATA
Repository: {scan_context.get('repo_name', 'Unknown')}
Security Score: {scan_context['scan_summary']['score'] if scan_context['scan_summary'] else 'N/A'}/100
Gate Result: {scan_context['scan_summary']['gate'].upper() if scan_context.get('scan_summary') and scan_context['scan_summary']['gate'] else 'N/A'}

## FINDINGS ({len(scan_context['findings'])} shown)
{findings_text}

## HISTORICAL CONTEXT
{scan_context.get('historical_note') or 'No previous scans available.'}

## SECURITY KNOWLEDGE BASE (RAG)
{rag_text or 'No relevant knowledge retrieved.'}"""

        # T-117: Stream via new google.genai async client
        async for chunk in await self.client.aio.models.generate_content_stream(
            model=settings.LLM_MODEL,
            contents=system_prompt + "\n\nDeveloper question: " + question,
            config=genai_types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=600,
            ),
        ):
            if chunk.text:
                yield chunk.text
