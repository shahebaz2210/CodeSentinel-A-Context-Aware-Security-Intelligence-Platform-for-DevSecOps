"""Repository routes — T-023."""

import httpx
from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Repository
from app.schemas.repository import RepositoryCreate, RepositoryResponse
import uuid

router = APIRouter()


async def get_github_repos(access_token: str) -> list[dict]:
    """Fetch authenticated user's GitHub repos via GitHub API — T-023."""
    repos = []
    page = 1
    async with httpx.AsyncClient() as client:
        while True:
            resp = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"per_page": 100, "page": page, "sort": "updated"},
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
            if len(data) < 100:
                break
    return repos


@router.get("/repos", summary="List authenticated user's GitHub repositories")
async def list_repos(
    authorization: str = Header(..., description="Bearer <github_access_token>"),
) -> list[dict]:
    """T-023: Returns the authenticated developer's GitHub repository list."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    repos = await get_github_repos(token)
    return [
        {
            "github_id": r["id"],
            "name": r["name"],
            "full_name": r["full_name"],
            "clone_url": r["clone_url"],
            "private": r["private"],
            "default_branch": r.get("default_branch", "main"),
            "owner": r["owner"]["login"],
            "description": r.get("description"),
            "language": r.get("language"),
            "updated_at": r.get("updated_at"),
        }
        for r in repos
    ]


@router.post("/repos/connect", summary="Connect a repository to CodeSentinel")
async def connect_repo(
    payload: RepositoryCreate,
    authorization: str = Header(...),
    db: Session = Depends(get_db),
) -> dict:
    """Register a GitHub repository in CodeSentinel's database."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")

    existing = db.query(Repository).filter(Repository.github_id == payload.github_id).first()
    if existing:
        return {"id": str(existing.id), "full_name": existing.full_name, "already_connected": True}

    repo = Repository(
        github_id=payload.github_id,
        name=payload.name,
        full_name=payload.full_name,
        clone_url=payload.clone_url,
        default_branch=payload.default_branch,
        owner_login=payload.owner_login,
        is_private=payload.is_private,
        github_access_token=token,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return {"id": str(repo.id), "full_name": repo.full_name, "already_connected": False}
