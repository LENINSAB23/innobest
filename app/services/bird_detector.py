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
        """Carga el modelo de IA desde app/models/ (prioriza best.onnx para mayor velocidad y compatibilidad, o best.pt)."""
        onnx_file = settings.MODELS_DIR / "best.onnx"
        pt_file = settings.MODELS_DIR / "best.pt"
        
        target_path = None
        if onnx_file.exists() and onnx_file.stat().st_size > 50000:
            target_path = onnx_file
            format_name = "ONNX Runtime (.onnx)"
        elif pt_file.exists() and pt_file.stat().st_size > 50000:
            target_path = pt_file
            format_name = "PyTorch (.pt)"

        if target_path:
            try:
                from ultralytics import YOLO
                logger.info(f"Cargando modelo de visión artificial ({format_name}) desde: {target_path}")
                self.model = YOLO(str(target_path))
                self.model_loaded = True
                self.model_path = target_path
                self.model_format = format_name
                self.model_classes = self.model.names if hasattr(self.model, "names") else {}
                self.model_task = getattr(self.model, "task", "classify")
                logger.info(f"¡Modelo {format_name} cargado con éxito! Tarea: {self.model_task}, Clases: {self.model_classes}")
                return
            except Exception as e:
                logger.error(f"Error cargando modelo {target_path}: {e}")
                self.model_loaded = False
        else:
            logger.warning(
                f"No se encontró archivo de modelo en {settings.MODELS_DIR}. "
                "Coloca 'best.onnx' o 'best.pt' para habilitar inferencia real."
            )
            self.model_loaded = False

    def predict_image(self, pil_image: Image.Image, conf_threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Ejecuta la inferencia sobre una imagen PIL.
        Soporta automáticamente tanto modelos de Clasificación (r.probs) como de Detección (r.boxes).
        """
        conf = conf_threshold or settings.CONFIDENCE_THRESHOLD
        width, height = pil_image.size
        detections: List[Dict[str, Any]] = []

        if self.model_loaded and self.model is not None:
            try:
                results = self.model.predict(
                    source=pil_image,
                    conf=conf,
                    verbose=False
                )
                
                for r in results:
                    # Caso A: Modelo de Detección de Objetos (con cajas delimitadoras)
                    if hasattr(r, "boxes") and r.boxes is not None and len(r.boxes) > 0:
                        for box in r.boxes:
                            xyxy = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])
                            if confidence < conf:
                                continue
                            class_id = int(box.cls[0])
                            raw_name = self.model_classes.get(class_id, f"Ave_{class_id}")
                            bird_info = get_bird_info(raw_name)
                            display_name = bird_info.get("common_name", raw_name.replace("_", " ").title())

                            detections.append({
                                "class_id": class_id,
                                "class_name": display_name,
                                "raw_class": raw_name,
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

                    # Caso B: Modelo de Clasificación (probabilidades por clase)
                    elif hasattr(r, "probs") and r.probs is not None:
                        top1_id = int(r.probs.top1)
                        top1_conf = float(r.probs.top1conf)
                        
                        if top1_conf >= conf:
                            raw_name = self.model_classes.get(top1_id, f"Ave_{top1_id}")
                            bird_info = get_bird_info(raw_name)
                            display_name = bird_info.get("common_name", raw_name.replace("_", " ").title())
                            
                            # Enmarcar el área visual del espécimen (estilo cuadro YOLO)
                            bx1 = int(width * 0.15)
                            by1 = int(height * 0.10)
                            bx2 = int(width * 0.85)
                            by2 = int(height * 0.90)

                            detections.append({
                                "class_id": top1_id,
                                "class_name": display_name,
                                "raw_class": raw_name,
                                "confidence": round(top1_conf, 4),
                                "confidence_pct": round(top1_conf * 100, 1),
                                "box": {
                                    "x1": bx1,
                                    "y1": by1,
                                    "x2": bx2,
                                    "y2": by2,
                                    "norm_x1": round(bx1 / width, 4),
                                    "norm_y1": round(by1 / height, 4),
                                    "norm_x2": round(bx2 / width, 4),
                                    "norm_y2": round(by2 / height, 4),
                                },
                                "bird_info": bird_info
                            })
            except Exception as e:
                logger.error(f"Error en inferencia de visión artificial: {e}")
        else:
            detections = self._simulate_or_standby(width, height)

        return {
            "image_size": {"width": width, "height": height},
            "detections_count": len(detections),
            "detections": detections,
            "model_active": self.model_loaded,
            "model_name": getattr(self, "model_format", "best.pt")
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
