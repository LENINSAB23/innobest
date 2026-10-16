"""
Esquemas Pydantic para validación y serialización de la API de InnoBest.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    norm_x1: float
    norm_y1: float
    norm_x2: float
    norm_y2: float

class BirdInfo(BaseModel):
    id: str
    common_name: str
    scientific_name: str
    family: str
    conservation_status: str
    status_code: str
    status_color: str
    huanuco_habitat: str
    diet: str
    description: str
    threats: str

class DetectionItem(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    confidence_pct: float
    box: BoundingBox
    bird_info: Dict[str, Any]
    is_demo: Optional[bool] = False

class WebcamFrameRequest(BaseModel):
    image_base64: str = Field(..., description="Cuadro de video codificado en base64 desde la cámara web")
    conf_threshold: Optional[float] = Field(0.45, ge=0.1, le=1.0)
    save_to_db: bool = Field(True, description="Indica si debe persistir los resultados en MongoDB Atlas")

class DetectionResponse(BaseModel):
    success: bool
    detections_count: int
    detections: List[Dict[str, Any]]
    model_active: bool
    model_name: str
    saved_to_db: bool
    record_id: Optional[str] = None
    message: Optional[str] = None
