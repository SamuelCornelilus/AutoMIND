# backend/app/config.py
# =====================================================================
# KONFIGURASI APLIKASI
# - Membaca .env jika ada
# - Mengambil SECRET_KEY, ALGORITHM, EXPIRE
# - Menentukan database URL (Postgres via Docker atau fallback SQLite)
# =====================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# 1) Load .env (jika ada)
# ---------------------------------------------------------------------
HERE = Path(__file__).resolve().parent.parent  # backend/app -> backend folder
DOTENV_PATH = HERE / ".env"
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)


# ---------------------------------------------------------------------
# 2) Helper functions
# ---------------------------------------------------------------------
def _getenv(key, default=None):
    val = os.getenv(key)
    return val if val is not None else default

def _getint(key, default):
    try:
        val = os.getenv(key)
        return int(val) if val is not None else default
    except Exception:
        return default


# ---------------------------------------------------------------------
# 3) JWT / Token settings
# ---------------------------------------------------------------------
SECRET_KEY = _getenv("SECRET_KEY", "replace-me-with-a-strong-secret-in-prod")
ALGORITHM = _getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _getint("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7)  # Default 7 hari


# ---------------------------------------------------------------------
# 4) DATABASE CONFIGURATION (Postgres via Docker atau fallback SQLite)
# ---------------------------------------------------------------------

# Jika Docker memberikan environment DATABASE_URL, kita pakai itu.
# Contoh Postgres:
#   postgres://automind:password@db:5432/automind
database_env = os.getenv("DATABASE_URL")

if database_env:
    SQLALCHEMY_DATABASE_URL = database_env.strip()
else:
    # fallback: SQLite lokal di dalam folder backend
    sqlite_path = HERE / "db.sqlite"
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{sqlite_path}"

# ---------------------------------------------------------------------
# 5) Flag debugging
# ---------------------------------------------------------------------
DEBUG = _getenv("DEBUG", "false").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------
# 6) Print config sekali saat startup (opsional)
# ---------------------------------------------------------------------
print(">> CONFIG LOADED")
print(f">> Using DB: {SQLALCHEMY_DATABASE_URL}")
print(f">> DEBUG: {DEBUG}")
