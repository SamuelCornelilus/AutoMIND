import os
import pytest

@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("AUTOMIND_BASE", "http://127.0.0.1:8000")
