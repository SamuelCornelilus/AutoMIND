# backend/app/create_tables.py
"""
Utility ringan untuk membuat tabel SQLite dari model-model SQLAlchemy.

Catatan:
 - Import model ditempatkan di dalam fungsi agar import side-effects
   (pendaftaran model ke Base.metadata) terjadi hanya saat fungsi dipanggil,
   dan tidak menyebabkan import cycle saat package diimport.
 - Kita memberikan `# noqa: F401` pada import model karena import
   tersebut digunakan untuk side-effect (tidak dipakai langsung).
"""
from .db import Base, engine


def create_tables():
    """Impor model lalu panggil create_all."""
    try:
        # diperlukan agar model terdaftar ke Base.metadata
        from . import models_auth  # noqa: F401
    except Exception:
        # environment CI atau container minimal mungkin tidak punya semua dep
        # Jangan hentikan eksekusi — cukup lanjutkan.
        pass

    try:
        from . import models_history  # noqa: F401
    except Exception:
        pass

    Base.metadata.create_all(bind=engine)
