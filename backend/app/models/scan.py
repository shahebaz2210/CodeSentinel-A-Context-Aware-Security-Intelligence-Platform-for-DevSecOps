"""Scan model — represents a single repository or PR scan event."""

import uuid
import enum
from sqlalchemy import String, Integer, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class ScanType(str, enum.Enum):
    REPO = "repo"
    PR = "pr"


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GateResult(str, enum.Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCK = "block"


class Scan(Base, TimestampMixin):
    """A single scan event for a repository or pull request."""

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_type: Mapped[ScanType] = mapped_column(
        SAEnum(ScanType, name="scan_type_enum"), nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus, name="scan_status_enum"), default=ScanStatus.PENDING, nullable=False
    )
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    git_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    security_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    gate_result: Mapped[GateResult | None] = mapped_column(
        SAEnum(GateResult, name="gate_result_enum"), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_check_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="scans")
    repository_context: Mapped["RepositoryContext | None"] = relationship(
        "RepositoryContext", back_populates="scan", uselist=False, cascade="all, delete-orphan"
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding", back_populates="scan", cascade="all, delete-orphan"
    )
    policy_result: Mapped["PolicyResult | None"] = relationship(
        "PolicyResult", back_populates="scan", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scan {self.id} [{self.scan_type}/{self.status}]>"
