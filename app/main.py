"""
Punto de Entrada Principal de InnoBest - Reconocimiento de Aves de Huánuco.
Servidor FastAPI con soporte asíncrono para inferencia por visión artificial,
gestión de base de datos MongoDB Atlas y entrega del frontend web interactivo.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import settings
from app.api.routes import router as api_router
from app.database import db_manager

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("innobest.main")

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS para permitir conexiones seguras
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas de archivos estáticos y plantillas
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Montar directorio estático
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Configurar motor de plantillas Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Incluir router de la API
app.include_router(api_router)

@app.get("/", response_class=HTMLResponse, summary="Página principal de la aplicación web")
async def index_view(request: Request):
    """Renderiza el dashboard interactivo de reconocimiento de aves."""
    stats = db_manager.get_statistics()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": settings.PROJECT_NAME,
            "connected_to_atlas": stats.get("connected_to_atlas", False),
            "status_message": stats.get("status_message", "Iniciando...")
        }
    )

@app.on_event("startup")
async def on_startup():
    logger.info("=============================================================")
    logger.info("   INNOBEST - RECONOCIMIENTO DE AVES DE HUÁNUCO INICIADO    ")
    logger.info("=============================================================")
    logger.info(f"Servidor: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Documentación Swagger: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"Estado MongoDB Atlas: {db_manager.connection_message}")
    logger.info("=============================================================")

@app.get("/health", summary="Chequeo de salud del servicio")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": db_manager.connection_message
    }
