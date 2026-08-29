"""FindingHistory model — tracks finding status across scans for Security Memory."""

import uuid
import enum
from sqlalchemy import ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class HistoryStatus(str, enum.Enum):
    NEW = "new"
    RECURRING = "recurring"
    UNCHANGED = "unchanged"
    RESOLVED = "resolved"


class FindingHistory(Base, TimestampMixin):
    """
    Records how a finding changed status between scans (Security Memory).
    Created by FindingDiffer after each scan completes.
    """

    __tablename__ = "finding_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    history_status: Mapped[HistoryStatus] = mapped_column(
        SAEnum(HistoryStatus, name="history_status_enum"), nullable=False
    )

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="history")

    def __repr__(self) -> str:
        return f"<FindingHistory finding={self.finding_id} status={self.history_status}>"
