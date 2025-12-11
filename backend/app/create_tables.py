# backend/app/create_tables.py
"""
Utility kecil untuk memastikan file DB & tabel dibuat.
Fungsi `create_db_and_tables()` diekspos agar main.py atau Docker entrypoint
bisa memanggilnya tanpa tergantung pada nama fungsi internal lainnya.
"""

import logging
from typing import Optional

from .db import (  # gunakan fungsi di db.py bila ada
    create_db_and_tables as _create_db_and_tables,
)

logger = logging.getLogger(__name__)


def create_db_and_tables(db_url: Optional[str] = None) -> str:
    """
    Wrapper yang memanggil implementasi pembuatan DB / tabel.
    Mengembalikan database URL / path yang digunakan (string).
    db_url argumen opsional disediakan untuk kompatibilitas jika diperlukan.
    """
    try:
        # Jika modul app.db menyediakan fungsi create_db_and_tables, pakai itu
        result = _create_db_and_tables()
        logger.info("Database & tables created by app.db.create_db_and_tables()")
        return result
    except Exception as exc:
        # Jika terjadi error, coba fallback: langsung panggil Base.metadata.create_all
        # (untuk situasi edge-case waktu container minimal)
        logger.exception(
            "create_db_and_tables: fallback path because primary call failed: %s", exc
        )
        try:
            # impor-lokal agar tidak membuat import cycle pada top-level
            from .db import Base, engine

            Base.metadata.create_all(bind=engine)
            logger.info(
                "Fallback: created tables via Base.metadata.create_all(bind=engine)"
            )
            # kembalikan default DATABASE_URL dari db.py jika tersedia
            from .db import DATABASE_URL

            return DATABASE_URL
        except Exception as exc2:
            logger.exception("Fallback create tables also failed: %s", exc2)
            raise
