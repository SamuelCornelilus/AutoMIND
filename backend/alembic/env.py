# backend/alembic/env.py
from __future__ import annotations

import os
import sys
import traceback
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# -------------------------------------------------------
# Masukkan root project ke sys.path agar app.* dapat diimport
# -------------------------------------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# -------------------------------------------------------
# Alembic Config object
# -------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------
# Ambil DATABASE_URL dari environment, atau fallback alembic.ini
# -------------------------------------------------------
env_db_url = os.getenv("DATABASE_URL")
if env_db_url:
    config.set_main_option("sqlalchemy.url", env_db_url)

# -------------------------------------------------------
# Import model modules supaya mereka mendaftarkan metadata ke Base
# Kita hanya mengimport untuk side-effect; gunakan noqa F401 agar linter tidak complain.
# -------------------------------------------------------
try:
    # import side-effect: models register themselves on Base.metadata
    import app.models_auth  # type: ignore # noqa: F401
except Exception:
    # laporkan tapi jangan crash
    import sys

    print("warning: gagal import app.models_auth", file=sys.stderr)
    traceback.print_exc()

try:
    import app.models_history  # type: ignore # noqa: F401
except Exception:
    pass

# -------------------------------------------------------
# Import Base metadata
# -------------------------------------------------------
try:
    from app.db import Base
except Exception as e:
    raise RuntimeError(f"Gagal import Base dari app.db: {e}")

target_metadata = Base.metadata


# -------------------------------------------------------
# Offline migration
# -------------------------------------------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -------------------------------------------------------
# Online migration
# -------------------------------------------------------
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
