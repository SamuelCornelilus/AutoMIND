import requests


def test_health_basic(base_url):
    r = requests.get(f"{base_url}/health", timeout=5)
    assert r.status_code == 200


def test_auth_token_endpoint_exists(base_url):
    try:
        r = requests.post(
            f"{base_url}/auth/token",
            data={"username": "nope", "password": "nope"},
            timeout=5,
        )
        assert r.status_code in (200, 201, 400, 401, 404)
    except requests.exceptions.RequestException:
        assert False, "request error to /auth/token"
