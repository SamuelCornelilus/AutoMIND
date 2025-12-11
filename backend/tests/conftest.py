# backend/tests/_conftest.py
import os
import time
import requests
import pytest

@pytest.fixture(scope="session")
def base_url():
    """
    Fixture untuk mengembalikan base URL API.
    Cek env var BASE, kalau tidak ada pakai default http://127.0.0.1:8000
    Juga menunggu /health sampai 15 detik.
    """
    url = os.environ.get("BASE", "http://127.0.0.1:8000").rstrip("/")
    health = f"{url}/health"

    for attempt in range(15):
        try:
            r = requests.get(health, timeout=2)
            if r.status_code == 200:
                return url
        except requests.RequestException:
            pass
        time.sleep(1)

    pytest.exit(f"Server tidak merespon {health} setelah 15 detik. Pastikan backend berjalan dan BASE benar.")
