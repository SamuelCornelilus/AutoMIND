# backend/app/create_tables.py
from .db import Base, engine
import os

def create_db_and_tables():
    """
    Membuat database dan tabel-tabel SQLAlchemy.
    Wajib mengimpor semua model agar tabelnya terdaftar.
    """

    # === WAJIB: impor semua model sebelum create_all ===
    from . import models_auth
    from . import models_history

    # Buat semua tabel
    Base.metadata.create_all(bind=engine)
    print(">> Database & tables created.")
