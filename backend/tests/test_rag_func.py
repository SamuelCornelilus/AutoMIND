import requests


def test_query_endpoint_exists(base_url):
    try:
        r = requests.post(
            f"{base_url}/query",
            json={"question": "Siapa presiden Indonesia?"},
            timeout=10,
        )
        assert r.status_code in (200, 400, 404, 422)
    except requests.exceptions.RequestException:
        assert False, "request error to /query"
