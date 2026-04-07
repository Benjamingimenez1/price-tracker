import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database.session import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.routes import auth, products

# ── Logging ─────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ── Lifespan (startup / shutdown) ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Price Tracker PRO")

    # Inicializar base de datos
    init_db()

    # Iniciar scheduler
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler failed: {e}")

    yield

    # Detener scheduler
    try:
        stop_scheduler()
    except Exception:
        pass

    logger.info("🛑 Shutting down")

# ── App ─────────────────────────────
app = FastAPI(
    title="Price Tracker PRO",
    version="1.0.0",
    lifespan=lifespan
)

# ── CORS ────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")

# ── Health check ────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}

# ── Frontend (si existe) ────────────
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
static_dir = os.path.join(frontend_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── SPA fallback ────────────────────
@app.get("/", include_in_schema=False)
@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str = ""):
    index_path = os.path.join(frontend_dir, "index.html")

    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"message": "API running"}