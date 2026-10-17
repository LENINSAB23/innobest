"""
Catálogo de información de las aves en peligro de extinción en Huánuco, Perú.
Incluye información taxonómica, estado de conservación (UICN), hábitats locales,
y características morfológicas clave para validación y enriquecimiento de predicciones.
"""

BIRDS_CATALOG = {
    "gallito de las rocas": {
        "id": "gallito_de_las_rocas",
        "common_name": "Gallito de las Rocas (Tunqui)",
        "scientific_name": "Rupicola peruvianus",
        "family": "Cotingidae",
        "conservation_status": "Ave Nacional del Perú / En Monitoreo Regional",
        "status_code": "VU",
        "status_color": "#ea580c",  # Naranja escarlata
        "huanuco_habitat": "Bosques nublados y quebradas rocosas del Parque Nacional Tingo María, Cueva de las Pavas, Carpish y valles de Huánuco (500 a 2,400 m s.n.m.).",
        "diet": "Frutos silvestres del estrato medio, bayas de laurisilva e insectos grandes.",
        "description": "Ave nacional del Perú (32 cm). El macho luce un plumaje anaranjado escarlata sumamente intenso y llamativo, alas y cola negras, y una prominente cresta en forma de disco sobre el pico. Famosos por sus leks o danzas de cortejo comunitario en los farallones rocosos.",
        "threats": "Deforestación por expansión agrícola y tala, pérdida de sitios de nidificación en cañones y tráfico ilegal de especies silvestres.",
        "keywords": ["gallito de las rocas", "gallito_de_las_rocas", "gallito", "rupicola", "rupicola peruvianus", "tunqui", "cock of the rock", "rocas", "trompetero"]
    },
    "matorralero tricolor": {
        "id": "matorralero_tricolor",
        "common_name": "Matorralero Tricolor",
        "scientific_name": "Atlapetes tricolor",
        "family": "Passerellidae",
        "conservation_status": "En Peligro / Endemismo Yungas",
        "status_code": "EN",
        "status_color": "#dc2626",  # Rojo/Naranja
        "huanuco_habitat": "Bosques nublados y matorrales montanos del Bosque de Protección de Carpish, Panao y cordilleras altas de Huánuco (1,800 a 3,200 m s.n.m.).",
        "diet": "Semillas, bayas e insectos que recolecta forrajeando en parejas o pequeños grupos en el estrato bajo.",
        "description": "Ave cantora de tamaño mediano (17 cm). Presenta un llamativo contraste: corona y nuca de tono amarillo ocre brillante, máscara facial negra profunda, garganta y vientre amarillo intenso, con dorso y cola pardo oliva oscuro.",
        "threats": "Fragmentación extrema del bosque de neblina de Carpish por la ampliación de la frontera agrícola (cultivo de papa y hortensias) y la construcción de vías.",
        "keywords": ["matorralero", "matorralero tricolor", "matorrelero", "matorrelero_tricolor", "matorrelero tricolor", "atlapetes", "tricolor", "pinzon tricolor", "motorrelero"]
    },
    "paujil": {
        "id": "paujil",
        "common_name": "Paujil del Huallaga",
        "scientific_name": "Crax globulosa / Mitu tuberosa",
        "family": "Cracidae",
        "conservation_status": "En Peligro Crítico (CR / EN)",
        "status_code": "CR",
        "status_color": "#b91c1c",  # Rojo oscuro
        "huanuco_habitat": "Bosques de várzea y terrazas aluviales a lo largo de los afluentes del río Huallaga y cuenca del Pachitea en Huánuco.",
        "diet": "Frutos grandes, brotes tiernos, hojas y semillas caídas de árboles del dosel.",
        "description": "Ave de gran envergadura (80 a 90 cm), elegante y majestuosa. Posee un plumaje negro carbón lustroso con reflejos azulados o violáceos, cresta rizada prominente de plumas eréctiles en la cabeza, abdomen blanco o castaño y una llamativa protuberancia carnosa roja o escarlata en la base del pico.",
        "threats": "Presión extrema por caza cinegética y de subsistencia por su abundante carne, además de la tala selectiva de árboles frutales nativos.",
        "keywords": ["paujil", "crax", "mitu", "curassow", "paujil comun", "paujil tuberoso"]
    }
}

def get_bird_info(class_name: str) -> dict:
    """Retorna la ficha técnica enriquecida para una clase detectada."""
    name_clean = class_name.lower().replace("_", " ").strip()
    
    # Búsqueda directa o por coincidencia de palabras clave
    for bird_id, info in BIRDS_CATALOG.items():
        if bird_id in name_clean or any(k in name_clean for k in info["keywords"]):
            return info
            
    # Default en caso de clase genérica
    return {
        "id": "desconocido",
        "common_name": class_name.capitalize(),
        "scientific_name": "Aves de Huánuco",
        "family": "N/A",
        "conservation_status": "Monitoreo Requerido",
        "status_code": "DD",
        "status_color": "#059669",
        "huanuco_habitat": "Región Huánuco, Perú",
        "diet": "Nativa",
        "description": f"Detección de especie clasificada como {class_name}.",
        "threats": "Requiere mayor registro de campo.",
        "keywords": [class_name]
    }
