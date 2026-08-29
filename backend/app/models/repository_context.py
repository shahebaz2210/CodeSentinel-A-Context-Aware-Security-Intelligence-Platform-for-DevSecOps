"""RepositoryContext model — structured metadata produced by Agent 1."""

import uuid
from sqlalchemy import Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base, TimestampMixin


class RepositoryContext(Base, TimestampMixin):
    """Structured metadata about a repository produced by the Repository Analysis Agent."""

    __tablename__ = "repository_contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    languages: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    frameworks: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    databases: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    authentication: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    file_tree_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    architecture_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="repository_context")

    def __repr__(self) -> str:
        return f"<RepositoryContext scan={self.scan_id} languages={self.languages}>"
