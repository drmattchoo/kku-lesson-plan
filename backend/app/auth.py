from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import RedirectResponse

from app.config import settings

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    # Explicit endpoints (no discovery-doc fetch) so /auth/login never needs network —
    # keeps it testable offline and matches "mock the LLM/network in tests" convention.
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _is_allowed(email: str) -> bool:
    return email.lower().endswith(f"@{settings.allowed_email_domain.lower()}")


@router.get("/login")
async def login(request: Request):
    if settings.base_url:
        # explicit, env-driven — never trust the incoming request's scheme here,
        # since most PaaS reverse proxies (Render/Railway/Fly) terminate TLS at the
        # edge and forward plain http, which would otherwise produce a callback URL
        # that doesn't match what's registered in the Google console.
        redirect_uri = f"{settings.base_url.rstrip('/')}/auth/callback"
    else:
        redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(
        request, redirect_uri, hd=settings.allowed_email_domain
    )


@router.get("/callback", name="auth_callback")
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    email = userinfo["email"]
    if not _is_allowed(email):
        raise HTTPException(
            status_code=401,
            detail=f"Only @{settings.allowed_email_domain} accounts are allowed",
        )

    request.session["user"] = {"email": email, "name": userinfo.get("name", "")}
    return RedirectResponse(url="/")


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


@router.get("/me")
def me(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_kku_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user or not _is_allowed(user.get("email", "")):
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
