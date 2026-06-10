import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.responses import Envelope, ok
from app.main import create_app

PUBLIC_ORIGIN = "https://example.com"
APP_ORIGIN = "https://app.example.com"
REAL_SECRET = "not-a-placeholder-secret-with-enough-length"


def make_client() -> TestClient:
    return TestClient(
        create_app(
            Settings(
                api_secret_key=REAL_SECRET,
                public_site_origin=PUBLIC_ORIGIN,
                app_origin=APP_ORIGIN,
            )
        )
    )


def test_public_cors_preflight_allows_site_origin_and_narrow_headers() -> None:
    response = make_client().options(
        "/api/v1/public/health",
        headers={
            "Origin": PUBLIC_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, X-Captcha-Token, Idempotency-Key",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == PUBLIC_ORIGIN
    assert response.headers["access-control-allow-methods"] == "GET, POST, OPTIONS"
    assert response.headers["access-control-allow-headers"] == (
        "Content-Type, X-Captcha-Token, Idempotency-Key"
    )


def test_public_cors_rejects_foreign_origin() -> None:
    response = make_client().options(
        "/api/v1/public/health",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_public_cors_rejects_unapproved_headers() -> None:
    response = make_client().options(
        "/api/v1/public/health",
        headers={
            "Origin": PUBLIC_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_non_public_api_exposes_no_browser_cors() -> None:
    response = make_client().get("/api/v1/health", headers={"Origin": PUBLIC_ORIGIN})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_security_headers_emit_on_every_response() -> None:
    response = make_client().get("/api/v1/health")

    assert response.headers["content-security-policy"].startswith("default-src 'self'")
    assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["strict-transport-security"].startswith("max-age=")
    assert response.headers["x-frame-options"] == "DENY"


def test_cookie_mutation_rejects_missing_or_foreign_origin() -> None:
    app = create_app(Settings(api_secret_key=REAL_SECRET, app_origin=APP_ORIGIN))
    _add_cookie_mutation_probe(app)
    client = TestClient(app)
    client.cookies.set("session", "value")

    missing_origin = client.post("/api/v1/test-cookie-mutation")
    foreign_origin = client.post(
        "/api/v1/test-cookie-mutation",
        headers={"Origin": "https://evil.example"},
    )

    assert missing_origin.status_code == 403
    assert foreign_origin.status_code == 403


def test_cookie_mutation_allows_app_origin_and_referer() -> None:
    app = create_app(Settings(api_secret_key=REAL_SECRET, app_origin=APP_ORIGIN))
    _add_cookie_mutation_probe(app)
    client = TestClient(app)
    client.cookies.set("session", "value")

    origin_response = client.post(
        "/api/v1/test-cookie-mutation",
        headers={"Origin": APP_ORIGIN},
    )
    referer_response = client.post(
        "/api/v1/test-cookie-mutation",
        headers={"Referer": f"{APP_ORIGIN}/settings"},
    )

    assert origin_response.status_code == 200
    assert referer_response.status_code == 200


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(env="production", api_secret_key="replace-me-with-a-long-random-secret")


def _add_cookie_mutation_probe(app: FastAPI) -> None:
    @app.post("/api/v1/test-cookie-mutation", response_model=Envelope[dict[str, str]])
    async def cookie_mutation_probe() -> Envelope[dict[str, str]]:
        return ok({"status": "ok"})
