"""Finding model — normalized output from security scanners."""

import uuid
import enum
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base, TimestampMixin


class FindingTool(str, enum.Enum):
    SEMGREP = "semgrep"
    GITLEAKS = "gitleaks"
    TRIVY = "trivy"


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(Base, TimestampMixin):
    """A normalized security finding from one of the scanner tools."""

    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # finding_key: stable identity for diffing across scans (tool+type+file+line)
    finding_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    tool: Mapped[FindingTool] = mapped_column(
        SAEnum(FindingTool, name="finding_tool_enum"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[FindingSeverity] = mapped_column(
        SAEnum(FindingSeverity, name="finding_severity_enum"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    code_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")
    analysis: Mapped["FindingAnalysis | None"] = relationship(
        "FindingAnalysis", back_populates="finding", uselist=False, cascade="all, delete-orphan"
    )
    remediation: Mapped["RemediationSuggestion | None"] = relationship(
        "RemediationSuggestion", back_populates="finding", uselist=False, cascade="all, delete-orphan"
    )
    history: Mapped[list["FindingHistory"]] = relationship(
        "FindingHistory", back_populates="finding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Finding {self.finding_type} [{self.severity}] {self.file_path}:{self.line_start}>"
