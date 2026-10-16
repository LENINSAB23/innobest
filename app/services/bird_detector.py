"""
Servicio de Detección de Aves con YOLO (Ultralytics).
Carga el modelo entrenado 'best.pt' para las 3 aves amenazadas de Huánuco:
1. Trompetero
2. Matorralero Tricolor
3. Paujil

Soporta inferencia sobre imágenes subidas y cuadros en tiempo real de la webcam (base64).
Incluye modo demostración / fallback si el archivo .pt aún no ha sido colocado en app/models/.
"""

import os
import io
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np

from app.config import settings
from app.services.birds_data import get_bird_info, BIRDS_CATALOG

logger = logging.getLogger("innobest.detector")

class BirdDetector:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.model_classes = {}
        self.load_model()

    def load_model(self):
        """Intenta cargar el modelo YOLO desde app/models/best.pt."""
        model_path = settings.MODEL_PATH
        if model_path.exists() and model_path.stat().st_size > 100000:
            try:
                from ultralytics import YOLO
                logger.info(f"Cargando modelo YOLO desde: {model_path}")
                self.model = YOLO(str(model_path))
                self.model_loaded = True
                self.model_classes = self.model.names if hasattr(self.model, "names") else {}
                logger.info(f"Modelo cargado exitosamente. Clases: {self.model_classes}")
                return
            except Exception as e:
                logger.error(f"Error cargando modelo YOLO {model_path}: {e}")
                self.model_loaded = False
        else:
            logger.warning(
                f"Archivo de modelo no encontrado en {model_path}. "
                "La aplicación funcionará en modo de espera/demostración hasta que se copie 'best.pt' en app/models/."
            )
            self.model_loaded = False

    def predict_image(self, pil_image: Image.Image, conf_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Ejecuta la predicción sobre una imagen PIL.
        Retorna la lista de detecciones enriquecidas con datos biológicos de Huánuco.
        """
        conf = conf_threshold or settings.CONFIDENCE_THRESHOLD
        width, height = pil_image.size
        detections: List[Dict[str, Any]] = []

        if self.model_loaded and self.model is not None:
            try:
                # Inferencia con YOLO
                results = self.model.predict(
                    source=pil_image,
                    conf=conf,
                    iou=settings.IOU_THRESHOLD,
                    verbose=False
                )
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model_classes.get(class_id, f"Ave_{class_id}")
                        
                        bird_info = get_bird_info(class_name)

                        detections.append({
                            "class_id": class_id,
                            "class_name": class_name,
                            "confidence": round(confidence, 4),
                            "confidence_pct": round(confidence * 100, 1),
                            "box": {
                                "x1": int(xyxy[0]),
                                "y1": int(xyxy[1]),
                                "x2": int(xyxy[2]),
                                "y2": int(xyxy[3]),
                                "norm_x1": round(xyxy[0] / width, 4),
                                "norm_y1": round(xyxy[1] / height, 4),
                                "norm_x2": round(xyxy[2] / width, 4),
                                "norm_y2": round(xyxy[3] / height, 4),
                            },
                            "bird_info": bird_info
                        })
            except Exception as e:
                logger.error(f"Error en inferencia YOLO: {e}")
        else:
            # Modo demostración / standby con simulación inteligente
            detections = self._simulate_or_standby(width, height)

        return {
            "image_size": {"width": width, "height": height},
            "detections_count": len(detections),
            "detections": detections,
            "model_active": self.model_loaded,
            "model_name": settings.MODEL_PATH.name
        }

    def _simulate_or_standby(self, width: int, height: int) -> List[Dict[str, Any]]:
        """
        No simula detecciones falsas para evitar etiquetar rostros u objetos como aves.
        Retorna lista vacía hasta que 'best.pt' esté presente en app/models/.
        """
        return []

    def decode_base64_frame(self, base64_str: str) -> Image.Image:
        """Decodifica un cuadro de video enviado desde el navegador en formato base64."""
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        image_bytes = base64.b64decode(base64_str)
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")

detector = BirdDetector()
