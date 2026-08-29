"""GitHub OAuth authentication routes — T-021, T-022."""

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Repository
import structlog

logger = structlog.get_logger()
router = APIRouter()

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/github", summary="Redirect to GitHub OAuth")
async def github_login() -> RedirectResponse:
    """T-021: Redirect developer to GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": "repo read:user",
        "state": "codesentinel",  # TODO: use CSRF token
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GITHUB_AUTH_URL}?{query}")


@router.get("/github/callback", summary="GitHub OAuth Callback")
async def github_callback(request: Request, code: str, state: str = "") -> dict:
    """T-022: Exchange OAuth code for access token and return session info."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_CALLBACK_URL,
            },
        )

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token in response")

    # Fetch GitHub user info
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user info")

    user_data = user_resp.json()
    logger.info("GitHub OAuth successful", user=user_data.get("login"))

    # Return token and user info (frontend stores in localStorage/cookie)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "github_user": {
            "id": user_data["id"],
            "login": user_data["login"],
            "avatar_url": user_data.get("avatar_url"),
            "name": user_data.get("name"),
        },
    }
