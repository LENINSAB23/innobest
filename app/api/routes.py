"""
Rutas de la API REST para InnoBest:
- Reconocimiento por Webcam en tiempo real
- Reconocimiento por Carga de Archivos (Fotos)
- Catálogo de las 3 Aves de Huánuco
- Historial y Estadísticas de MongoDB
- Estado del Sistema y Recarga del Modelo
"""

import io
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from PIL import Image

from app.api.schemas import (
    WebcamFrameRequest,
    DetectionResponse,
    BirdInfo
)
from app.services.bird_detector import detector
from app.services.birds_data import BIRDS_CATALOG, get_bird_info
from app.database import db_manager

logger = logging.getLogger("innobest.routes")
router = APIRouter(prefix="/api", tags=["Reconocimiento de Aves"])

@router.get("/birds", summary="Catálogo de las 3 aves en peligro de extinción en Huánuco")
async def get_birds_catalog():
    """Retorna la lista y fichas técnicas de las 3 aves amenazadas."""
    return {
        "region": "Huánuco, Perú",
        "total_species": len(BIRDS_CATALOG),
        "birds": list(BIRDS_CATALOG.values())
    }

@router.post("/detect/webcam", response_model=DetectionResponse, summary="Detección en tiempo real por Webcam")
async def detect_webcam_frame(payload: WebcamFrameRequest):
    """
    Procesa un cuadro de video enviado desde la cámara de la laptop.
    Si detecta alguna de las aves y 'save_to_db' está activo, lo almacena en MongoDB.
    """
    try:
        pil_image = detector.decode_base64_frame(payload.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al decodificar imagen base64: {e}")

    result = detector.predict_image(pil_image, conf_threshold=payload.conf_threshold)
    detections = result["detections"]
    
    record_id = None
    saved_to_db = False

    # Guardar en MongoDB Atlas si se detectaron aves y el usuario lo solicitó
    if payload.save_to_db and detections:
        try:
            top_bird = detections[0]
            detection_record = {
                "source": "webcam",
                "bird_name": top_bird["class_name"],
                "bird_id": top_bird["bird_info"]["id"],
                "confidence": top_bird["confidence"],
                "confidence_pct": top_bird["confidence_pct"],
                "conservation_status": top_bird["bird_info"]["conservation_status"],
                "box": top_bird["box"],
                "detections_count": len(detections),
                "is_demo": top_bird.get("is_demo", False)
            }
            record_id = db_manager.save_detection(detection_record)
            saved_to_db = True
        except Exception as e:
            logger.error(f"Error al persistir detección de webcam en MongoDB: {e}")

    return DetectionResponse(
        success=True,
        detections_count=len(detections),
        detections=detections,
        model_active=result["model_active"],
        model_name=result["model_name"],
        saved_to_db=saved_to_db,
        record_id=record_id,
        message="Inferencia de webcam procesada exitosamente."
    )

@router.post("/detect/upload", response_model=DetectionResponse, summary="Detección sobre foto subida")
async def detect_uploaded_image(
    file: UploadFile = File(..., description="Archivo de imagen (JPG, PNG, JPEG, WEBP)"),
    conf_threshold: Optional[float] = Form(0.45),
    save_to_db: Optional[bool] = Form(True)
):
    """
    Recibe una fotografía subida por el usuario, ejecuta el modelo YOLO y retorna
    las coordenadas de la caja delimitadora, la especie y sus detalles de conservación.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo proporcionado no es una imagen válida.")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo abrir la imagen: {e}")

    result = detector.predict_image(pil_image, conf_threshold=conf_threshold)
    detections = result["detections"]

    record_id = None
    saved_to_db = False

    if save_to_db and detections:
        try:
            top_bird = detections[0]
            detection_record = {
                "source": "upload",
                "filename": file.filename,
                "bird_name": top_bird["class_name"],
                "bird_id": top_bird["bird_info"]["id"],
                "confidence": top_bird["confidence"],
                "confidence_pct": top_bird["confidence_pct"],
                "conservation_status": top_bird["bird_info"]["conservation_status"],
                "box": top_bird["box"],
                "detections_count": len(detections),
                "is_demo": top_bird.get("is_demo", False)
            }
            record_id = db_manager.save_detection(detection_record)
            saved_to_db = True
        except Exception as e:
            logger.error(f"Error persistiendo detección de imagen en MongoDB: {e}")

    return DetectionResponse(
        success=True,
        detections_count=len(detections),
        detections=detections,
        model_active=result["model_active"],
        model_name=result["model_name"],
        saved_to_db=saved_to_db,
        record_id=record_id,
        message=f"Imagen '{file.filename}' analizada con éxito."
    )

@router.get("/history", summary="Historial de detecciones guardadas en MongoDB Atlas")
async def get_history(limit: int = 25):
    """Retorna las detecciones más recientes guardadas en la base de datos."""
    records = db_manager.get_recent_detections(limit=limit)
    return {
        "total": len(records),
        "records": records,
        "database_status": db_manager.connection_message,
        "atlas_connected": db_manager.is_connected
    }

@router.get("/stats", summary="Estadísticas de monitoreo y estado de conexión")
async def get_statistics():
    """Retorna conteos agregados por especie y estado de conexión a MongoDB Atlas."""
    stats = db_manager.get_statistics()
    stats["model_active"] = detector.model_loaded
    stats["model_name"] = detector.model.names if detector.model_loaded else "best.pt (Standby)"
    return stats

@router.post("/model/reload", summary="Recargar modelo YOLO tras colocar best.pt")
async def reload_model():
    """Vuelve a chequear el directorio de modelos para cargar best.pt sin reiniciar el servidor."""
    detector.load_model()
    return {
        "model_loaded": detector.model_loaded,
        "model_classes": detector.model_classes,
        "message": "Modelo recargado exitosamente" if detector.model_loaded else "No se encontró best.pt en app/models/"
    }
