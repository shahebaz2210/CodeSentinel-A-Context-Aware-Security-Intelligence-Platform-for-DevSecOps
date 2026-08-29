"""Repository model — represents a GitHub repository connected to CodeSentinel."""

import uuid
from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    """A GitHub repository that has been connected for scanning."""

    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    clone_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    owner_login: Mapped[str] = mapped_column(String(255), nullable=False)
    is_private: Mapped[bool] = mapped_column(default=False, nullable=False)
    github_access_token: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Relationships
    scans: Mapped[list["Scan"]] = relationship("Scan", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Repository {self.full_name}>"
