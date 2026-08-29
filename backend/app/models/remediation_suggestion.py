"""RemediationSuggestion model — AI-generated fix with patch validation status."""

import uuid
import enum
from sqlalchemy import Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class ValidationStatus(str, enum.Enum):
    NOT_RUN = "not_run"
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"


class RemediationSuggestion(Base, TimestampMixin):
    """
    AI-generated remediation suggestion for a finding.
    validation_status tracks the Patch Validation pipeline result.
    Suggestions MUST NOT be trusted until validation_status == 'pass'.
    """

    __tablename__ = "remediation_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    secure_coding_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[ValidationStatus] = mapped_column(
        SAEnum(ValidationStatus, name="validation_status_enum"),
        default=ValidationStatus.NOT_RUN,
        nullable=False,
    )
    validation_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_celery_task_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="remediation")

    def __repr__(self) -> str:
        return f"<RemediationSuggestion finding={self.finding_id} validation={self.validation_status}>"
