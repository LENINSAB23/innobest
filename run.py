"""
Script de inicio directo para InnoBest - Reconocimiento de Aves de Huánuco.
Ejecutar con: python run.py
"""

import sys
import uvicorn
from app.config import settings

def main():
    print("=" * 65)
    print(" [INNOBEST] Monitoreo de Aves Amenazadas en Huanuco, Peru")
    print("=" * 65)
    print(f" -> Servidor Web:      http://{settings.HOST}:{settings.PORT}")
    print(f" -> Documentacion API: http://{settings.HOST}:{settings.PORT}/docs")
    print(f" -> Presiona CTRL + C para detener el servidor.")
    print("=" * 65)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

if __name__ == "__main__":
    main()
