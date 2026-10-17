"""
Gestor de Base de Datos MongoDB Atlas para InnoBest.
Provee conexión resiliente a MongoDB con soporte para colección de detecciones
en tiempo real y fallback a almacenamiento local si Atlas aún no está enlazado.
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger("innobest.database")
logging.basicConfig(level=logging.INFO)

LOCAL_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "detections_fallback.json"
LOCAL_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

class MongoDBManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False
        self.connection_message = "No inicializado"
        self._init_connection()

    def _init_connection(self):
        uri = settings.MONGODB_URI
        if not uri or "<password>" in uri:
            self.is_connected = False
            self.connection_message = "Credenciales pendientes en .env"
            logger.warning("URI de MongoDB no configurada correctamente.")
            return

        try:
            # Timeout corto de 4 segundos para no bloquear la app si Atlas no responde
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=4000,
                connectTimeoutMS=4000,
                socketTimeoutMS=4000,
                appname="InnoBestHuanuco"
            )
            # Verificar con ping
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            self.connection_message = "Conectado a MongoDB Atlas (Cluster0)"
            logger.info("¡Conexión exitosa a MongoDB Atlas!")
            
            # Crear índices para consultas rápidas
            self.db[settings.COLLECTION_DETECTIONS].create_index([("timestamp", DESCENDING)])
            self.db[settings.COLLECTION_DETECTIONS].create_index([("bird_id", 1)])
        except ServerSelectionTimeoutError as e:
            self.is_connected = False
            self.connection_message = "Atlas no disponible (guardando localmente)"
            logger.warning(f"No se pudo conectar a MongoDB Atlas: {e}. Activando modo local.")
        except Exception as e:
            self.is_connected = False
            self.connection_message = f"Error MongoDB: {str(e)[:50]}"
            logger.error(f"Error al conectar con MongoDB: {e}")

    def reconnect(self):
        """Recarga la configuración desde .env y reintenta conectar con MongoDB Atlas."""
        try:
            from dotenv import load_dotenv
            load_dotenv(settings.BASE_DIR / ".env", override=True)
            settings.MONGODB_URI = os.getenv("MONGODB_URI", settings.MONGODB_URI)
            settings.DATABASE_NAME = os.getenv("DATABASE_NAME", settings.DATABASE_NAME)
            settings.COLLECTION_DETECTIONS = os.getenv("COLLECTION_NAME", "Historial-Aves-Identificados")
            self._init_connection()
        except Exception as e:
            logger.error(f"Error al reconectar MongoDB: {e}")
        return self.is_connected

    def save_detection(self, detection_data: Dict[str, Any]) -> str:
        """Guarda un registro de detección en MongoDB o en fallback local."""
        # Agregar timestamp ISO y legible
        now = datetime.now(timezone.utc)
        record = {
            **detection_data,
            "timestamp": now,
            "timestamp_str": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "region": "Huánuco, Perú"
        }

        if self.is_connected and self.db is not None:
            try:
                res = self.db[settings.COLLECTION_DETECTIONS].insert_one(record)
                return str(res.inserted_id)
            except Exception as e:
                logger.error(f"Error guardando en MongoDB Atlas: {e}. Guardando localmente.")

        # Fallback local
        return self._save_local(record)

    def _save_local(self, record: Dict[str, Any]) -> str:
        """Almacena el registro en un archivo JSON local si MongoDB no está conectado."""
        try:
            records = []
            if LOCAL_DATA_FILE.exists():
                with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
                    try:
                        records = json.load(f)
                    except json.JSONDecodeError:
                        records = []

            # Serializar datetime a string
            record_copy = dict(record)
            if isinstance(record_copy.get("timestamp"), datetime):
                record_copy["timestamp"] = record_copy["timestamp"].isoformat()

            import uuid
            rec_id = str(uuid.uuid4())
            record_copy["_id"] = rec_id
            records.insert(0, record_copy)
            
            # Limitar a los últimos 500 registros locales
            records = records[:500]

            with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

            return rec_id
        except Exception as e:
            logger.error(f"Error en fallback local: {e}")
            return "local_fallback_error"

    def get_recent_detections(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Recupera las detecciones más recientes."""
        if self.is_connected and self.db is not None:
            try:
                cursor = self.db[settings.COLLECTION_DETECTIONS].find().sort("timestamp", DESCENDING).limit(limit)
                results = []
                for doc in cursor:
                    doc["_id"] = str(doc["_id"])
                    if isinstance(doc.get("timestamp"), datetime):
                        doc["timestamp"] = doc["timestamp"].isoformat()
                    results.append(doc)
                return results
            except Exception as e:
                logger.error(f"Error consultando MongoDB Atlas: {e}")

        # Fallback local
        if LOCAL_DATA_FILE.exists():
            try:
                with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data[:limit]
            except Exception:
                return []
        return []

    def get_statistics(self) -> Dict[str, Any]:
        """Calcula estadísticas generales de detecciones por especie."""
        stats = {
            "total_detections": 0,
            "species_counts": {
                "gallito_de_las_rocas": 0,
                "matorralero_tricolor": 0,
                "paujil": 0,
                "trompetero": 0,
                "otro": 0
            },
            "connected_to_atlas": self.is_connected,
            "status_message": self.connection_message,
            "last_detection": None
        }

        recent = self.get_recent_detections(limit=100)
        stats["total_detections"] = len(recent)
        if recent:
            stats["last_detection"] = recent[0].get("timestamp_str") or recent[0].get("timestamp")

        for r in recent:
            b_id = r.get("bird_id", "otro")
            if b_id in stats["species_counts"]:
                stats["species_counts"][b_id] += 1
            else:
                stats["species_counts"]["otro"] += 1

        return stats

db_manager = MongoDBManager()
