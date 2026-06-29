from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

import app.auth as auth_module
from app.main import app

client = TestClient(app)


def _redirect_uri_param(location: str) -> str:
    return parse_qs(urlparse(location).query)["redirect_uri"][0]


def _mock_google_token(monkeypatch, *, email: str, email_verified: bool = True, name: str = "Test User"):
    token = {
        "userinfo": {"email": email, "email_verified": email_verified, "name": name}
    }
    monkeypatch.setattr(
        auth_module.oauth.google, "authorize_access_token", AsyncMock(return_value=token)
    )


def test_login_redirects_to_google_without_hitting_network():
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)
    assert "accounts.google.com" in resp.headers["location"]


def test_login_redirect_uri_derived_from_request_when_base_url_unset():
    assert auth_module.settings.base_url == ""  # default in this test env

    resp = client.get("/auth/login", follow_redirects=False)

    redirect_uri = _redirect_uri_param(resp.headers["location"])
    assert redirect_uri.endswith("/auth/callback")
    assert redirect_uri.startswith("http://")  # TestClient's default scheme


def test_login_redirect_uri_uses_base_url_when_configured(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "base_url", "https://lesson-plan-staging.onrender.com")

    resp = client.get("/auth/login", follow_redirects=False)

    redirect_uri = _redirect_uri_param(resp.headers["location"])
    assert redirect_uri == "https://lesson-plan-staging.onrender.com/auth/callback"


def test_login_redirect_uri_strips_trailing_slash_from_base_url(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "base_url", "https://lesson-plan-staging.onrender.com/")

    resp = client.get("/auth/login", follow_redirects=False)

    redirect_uri = _redirect_uri_param(resp.headers["location"])
    assert redirect_uri == "https://lesson-plan-staging.onrender.com/auth/callback"


def test_callback_accepts_kku_email_and_sets_session(monkeypatch):
    _mock_google_token(monkeypatch, email="instructor@kku.ac.th")

    resp = client.get("/auth/callback", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "instructor@kku.ac.th"


def test_callback_rejects_non_kku_domain(monkeypatch):
    _mock_google_token(monkeypatch, email="instructor@gmail.com")

    resp = client.get("/auth/callback")
    assert resp.status_code == 401


def test_callback_rejects_unverified_email(monkeypatch):
    _mock_google_token(monkeypatch, email="instructor@kku.ac.th", email_verified=False)

    resp = client.get("/auth/callback")
    assert resp.status_code == 401


def test_protected_route_requires_login():
    anon_client = TestClient(app)
    resp = anon_client.get("/api/render-proof")
    assert resp.status_code == 401


def test_protected_route_allows_kku_user(monkeypatch):
    _mock_google_token(monkeypatch, email="instructor@kku.ac.th")
    logged_in_client = TestClient(app)
    logged_in_client.get("/auth/callback", follow_redirects=False)

    resp = logged_in_client.get("/api/render-proof")
    assert resp.status_code == 200
