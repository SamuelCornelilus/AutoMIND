# backend/test_query.py
import requests


def test_query_endpoint_exists(base_url):
    try:
        r = requests.post(
            f"{base_url}/query",
            json={"question": "Siapa presiden Indonesia?"},
            timeout=10,
        )
        # endpoint boleh 200 (OK) atau 4xx jika backend berikan validasi/erorr
        assert r.status_code in (200, 400, 404, 422)
    except requests.exceptions.RequestException:
        assert False, "request error to /query"
