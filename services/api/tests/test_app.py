from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

REAL_SECRET = "not-a-placeholder-secret-with-enough-length"


def test_create_app() -> None:
    app = create_app()

    assert app.title == "SaaS Template API"


def test_health_returns_enveloped_response() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "data": {"status": "ok"},
        "error": None,
        "meta": {},
    }


def test_openapi_documents_health_envelope() -> None:
    spec = create_app().openapi()
    health_response = spec["paths"]["/api/v1/health"]["get"]["responses"]["200"]

    assert health_response["content"]["application/json"]["schema"]["$ref"].startswith(
        "#/components/schemas/Envelope_HealthData_"
    )


def test_api_docs_disabled_by_default_in_production() -> None:
    app = create_app(
        Settings(env="production", expose_api_docs=False, api_secret_key=REAL_SECRET)
    )
    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_can_be_enabled_in_production() -> None:
    app = create_app(Settings(env="production", expose_api_docs=True, api_secret_key=REAL_SECRET))
    client = TestClient(app)

    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
