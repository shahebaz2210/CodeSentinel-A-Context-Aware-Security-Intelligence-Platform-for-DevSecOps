"""FindingAnalysis model — AI-produced analysis and deterministic risk score per finding."""

import uuid
from sqlalchemy import Text, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base, TimestampMixin


class FindingAnalysis(Base, TimestampMixin):
    """
    Stores the Risk & Validation Agent output + deterministic risk engine score per finding.

    IMPORTANT: The risk_score field is computed by DeterministicRiskEngine,
    NOT by the LLM. The LLM produces only the structured risk_factors (exploitability,
    impact, confidence, exposure, business_impact). This separation is intentional.
    """

    __tablename__ = "finding_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Agent 4 LLM outputs (structured risk factors only — NOT the final score)
    is_true_positive: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    exploitability: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)  # 0-10
    impact: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)  # 0-10
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)  # 0-10
    exposure: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)  # 0-10
    business_impact: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)  # 0-10

    # Deterministic risk engine output (computed, not LLM-generated)
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)  # 0-100

    # Agent 3 (Security Intelligence / RAG) outputs
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    attack_scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    owasp_refs: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    cwe_refs: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    security_recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<FindingAnalysis finding={self.finding_id} risk_score={self.risk_score}>"
