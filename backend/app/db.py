# app/db.py
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# lokasi file sqlite (relatif ke project)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app/
SQLITE_PATH = os.path.join(BASE_DIR, "db.sqlite")
DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

# engine (sqlite + multithreading)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model (untuk deklarative models)
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
        from . import models_auth     # user table
    except Exception:
        pass
    try:
        from . import models_history  # history table
    except Exception:
        pass

    # Buat file DB dan tabel
    Base.metadata.create_all(bind=engine)
    return SQLITE_PATH
