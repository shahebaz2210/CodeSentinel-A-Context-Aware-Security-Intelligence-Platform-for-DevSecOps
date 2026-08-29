"""Pydantic schemas for Repository."""

import uuid
from pydantic import BaseModel


class RepositoryCreate(BaseModel):
    github_id: int
    name: str
    full_name: str
    clone_url: str
    default_branch: str = "main"
    owner_login: str
    is_private: bool = False


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    github_id: int
    name: str
    full_name: str
    clone_url: str
    default_branch: str
    owner_login: str
    is_private: bool

    class Config:
        from_attributes = True
