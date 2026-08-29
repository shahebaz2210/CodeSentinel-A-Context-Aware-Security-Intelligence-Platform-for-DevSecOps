"""
Pydantic response schemas for all API endpoints — T-112.
These are the source-of-truth for API response shapes.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Repository ────────────────────────────────────────────────────────────────

class RepositoryResponse(BaseModel):
    id: UUID
    github_id: int
    name: str
    full_name: str
    clone_url: str
    default_branch: str
    owner_login: str
    is_private: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Scan ──────────────────────────────────────────────────────────────────────

class ScanResponse(BaseModel):
    scan_id: UUID = Field(alias="id")
    repository_id: UUID
    scan_type: str
    status: str
    pr_number: int | None = None
    git_ref: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    security_score: Decimal | None = None
    gate_result: str | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ScanHistoryItem(BaseModel):
    scan_id: UUID = Field(alias="id")
    scan_type: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    security_score: Decimal | None = None
    gate_result: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class PaginatedScans(BaseModel):
    total: int
    page: int
    limit: int
    scans: list[ScanHistoryItem]


# ── Finding Summary (for list views) ──────────────────────────────────────────

class FindingSummaryResponse(BaseModel):
    id: UUID
    scan_id: UUID
    finding_key: str
    tool: str
    finding_type: str
    severity: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    message: str
    risk_score: Decimal | None = None
    is_true_positive: bool | None = None
    history_status: str | None = None

    model_config = {"from_attributes": True}


# ── Finding Detail (full) ────────────────────────────────────────────────────

class FindingDetailResponse(FindingSummaryResponse):
    rule_id: str | None = None
    code_snippet: str | None = None
    raw_output: dict[str, Any] | None = None

    # From analysis join
    exploitability: Decimal | None = None
    impact: Decimal | None = None
    confidence: Decimal | None = None
    exposure: Decimal | None = None
    business_impact: Decimal | None = None
    root_cause: str | None = None
    attack_scenario: str | None = None
    ai_explanation: str | None = None
    owasp_refs: list[str] = []
    cwe_refs: list[str] = []
    security_recommendations: str | None = None

    # From remediation join
    suggested_fix: str | None = None
    secure_coding_guidance: str | None = None
    fix_explanation: str | None = None
    validation_status: str | None = None

    model_config = {"from_attributes": True}


# ── Policy Result ─────────────────────────────────────────────────────────────

class PolicyResultResponse(BaseModel):
    gate: str
    triggered_rules: list[str] = []
    findings_summary: dict[str, Any] = {}

    model_config = {"from_attributes": True}


# ── Trend ─────────────────────────────────────────────────────────────────────

class TrendItem(BaseModel):
    scan_id: UUID
    date: datetime
    security_score: Decimal | None = None
    gate_result: str | None = None
    new_findings: int = 0
    resolved_findings: int = 0
    recurring_findings: int = 0
    total_findings: int = 0

    model_config = {"from_attributes": True}


# ── Create requests ────────────────────────────────────────────────────────────

class ConnectRepoRequest(BaseModel):
    github_id: int
    name: str
    full_name: str
    clone_url: str
    default_branch: str = "main"
    owner_login: str
    is_private: bool = False


class AssistantQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    scan_id: str | None = None
    finding_id: str | None = None


# ── Scan creation ──────────────────────────────────────────────────────────────

class ScanCreatedResponse(BaseModel):
    scan_id: UUID
    status: str
    celery_task_id: str | None = None

    model_config = {"from_attributes": True}


# ── Validation ────────────────────────────────────────────────────────────────

class ValidationTriggerResponse(BaseModel):
    task_id: str
    finding_id: UUID
    suggestion_id: UUID | None = None
    message: str = "Validation task enqueued"
