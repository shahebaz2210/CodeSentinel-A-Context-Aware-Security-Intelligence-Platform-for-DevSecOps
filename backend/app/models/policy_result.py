"""PolicyResult model — deterministic PASS/WARNING/BLOCK gate result per scan."""

import uuid
from sqlalchemy import Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base, TimestampMixin
from .scan import GateResult


class PolicyResult(Base, TimestampMixin):
    """
    The deterministic Security Policy Gate result for a scan.
    Produced by PolicyEngine.evaluate() — NOT by the LLM.
    The LLM may only explain this result, never decide it.
    """

    __tablename__ = "policy_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    gate_result: Mapped[GateResult] = mapped_column(
        SAEnum(GateResult, name="gate_result_enum", create_constraint=False),
        nullable=False,
    )
    triggered_rules: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    findings_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="policy_result")

    def __repr__(self) -> str:
        return f"<PolicyResult scan={self.scan_id} gate={self.gate_result}>"
