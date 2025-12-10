# backend/app/main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from .create_tables import create_db_and_tables
from .auth import router as auth_router

# rag router: kalau Anda punya app/rag.py yang mendefinisikan `router = APIRouter(prefix="/rag", ...)`
# maka kita sertakan. Jika belum ada, baris include_router(rag_router) tidak boleh dieksekusi.
try:
    from .rag import router as rag_router
    HAS_RAG = True
except Exception:
    HAS_RAG = False

app = FastAPI(title="AutoMIND Retrieval API")

# -----------------------
# CORS (untuk dev frontend)
# -----------------------
# Sesuaikan origins sesuai alamat frontend Anda. Untuk dev default:
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create DB & tables on startup (safe to run multiple times)
create_db_and_tables()

# include routers (router sendiri sudah punya prefix masing-masing)
app.include_router(auth_router)
if HAS_RAG:
    app.include_router(rag_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- custom openapi to add BearerAuth UI (single input box) ---
def custom_openapi():
    """
    Membuat OpenAPI schema yang menambahkan komponen security BearerAuth.
    Kita juga menandai endpoint yang memerlukan security secara default kecuali daftar pengecualian.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="AutoMIND Retrieval API (modified OpenAPI to use Bearer auth)",
        routes=app.routes,
    )

    # tambahkan Bearer security scheme
    openapi_schema.setdefault("components", {})
    openapi_schema["components"].setdefault("securitySchemes", {})
    # beri nama "BearerAuth" sehingga Swagger UI menampilkan satu kotak input
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }

    # daftar path yang TIDAK harus diberi security otomatis (boleh ditambah)
    exclude_paths = {
        "/auth/register",  # register publik
        "/auth/login",     # login publik
        "/health",         # health check publik
        "/openapi.json",   # schema
        "/docs",           # docs UI
        "/redoc",          # redoc UI (jika ada)
    }

    # set security untuk semua path/method kecuali yang dikecualikan
    for path, path_item in openapi_schema.get("paths", {}).items():
        if path in exclude_paths:
            continue
        for method_name, method_spec in list(path_item.items()):
            # hanya tambahkan jika bukan operation yang sudah punya security
            if "security" not in method_spec:
                method_spec["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# pasang custom openapi
app.openapi = custom_openapi
