from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.auth as auth_module
from app.main import app

client = TestClient(app)


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
