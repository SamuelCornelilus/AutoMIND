# backend/app/db.py
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# lokasi file sqlite (relatif ke project)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
SQLITE_PATH = os.path.join(BASE_DIR, "db.sqlite")
DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

# engine (sqlite + multithreading)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model (untuk declarative models)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI: yield sebuah DB session.
    Gunakan di endpoint: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    """
    Membuat file sqlite dan semua tabel berdasarkan model-model SQLAlchemy yang
    terdaftar pada Base.metadata. Panggilan aman untuk dipanggil beberapa kali.
    """
    # Pastikan direktori ada (biasanya app/)
    db_dir = os.path.dirname(SQLITE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    # IMPORT semua module model di sini supaya mereka mendaftarkan metadata ke Base
    # (Jika Anda punya models lain, tambahkan di sini)
    try:
        # import hanya untuk side-effect (mendaftarkan model ke Base.metadata)
        from . import models_auth  # type: ignore # noqa: F401
    except Exception:
        import sys
        import traceback

        print("warning: import backend.app.models_auth gagal", file=sys.stderr)
        traceback.print_exc()

    try:
        from . import models_history  # type: ignore # noqa: F401
    except Exception:
        pass

    # Buat file DB dan tabel
    Base.metadata.create_all(bind=engine)
    return SQLITE_PATH
