import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "InnoBest - Reconocimiento de Aves en Peligro (Huánuco)"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema Web con IA para la detección y monitoreo en tiempo real de aves amenazadas en el departamento de Huánuco, Perú."

    # Model configuration
    MODELS_DIR: Path = BASE_DIR / "app" / "models"
    MODEL_PATH: Path = MODELS_DIR / os.getenv("MODEL_NAME", "best.pt")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
    IOU_THRESHOLD: float = float(os.getenv("IOU_THRESHOLD", "0.45"))

    # MongoDB Atlas configuration
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://leninsabino27_db_user:5L5GnftQlls0Ejnx@cluster0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "aves_huanuco_db")
    COLLECTION_DETECTIONS: str = "detecciones_tiempo_real"
    COLLECTION_UPLOADS: str = "analisis_imagenes"
    
    # Server host & port
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
