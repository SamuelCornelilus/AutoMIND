import requests


def test_docs(base_url):
    r = requests.get(f"{base_url}/docs", timeout=5)
    assert r.status_code == 200
