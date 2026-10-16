"""
Catálogo de información de las aves en peligro de extinción en Huánuco, Perú.
Incluye información taxonómica, estado de conservación (UICN), hábitats locales,
y características morfológicas clave para validación y enriquecimiento de predicciones.
"""

BIRDS_CATALOG = {
    "trompetero": {
        "id": "trompetero",
        "common_name": "Trompetero del Huallaga",
        "scientific_name": "Psophia leucoptera / Psophia crepitans",
        "family": "Psophiidae",
        "conservation_status": "Vulnerable / En Riesgo Regional",
        "status_code": "VU",
        "status_color": "#d97706",  # Ámbar
        "huanuco_habitat": "Bosques húmedos tropicales de la cuenca del Huallaga, Parque Nacional Tingo María y bosques de Puerto Inca.",
        "diet": "Frutos caídos, semillas, artrópodos y pequeños invertebrados del sotobosque.",
        "description": "Ave gregaria y terrestre de unos 45-52 cm de longitud con joroba pronunciada. Plumaje denso de color negro brillante con reflejos morados en el pecho y una capa grisácea o blanca en la espalda y alas. Emiten vocalizaciones profundas y resonantes similares a un tambor o trompeta.",
        "threats": "Cacería intensiva para consumo humano debido a su mansedumbre y desplazamiento en bandadas por el suelo, sumado a la pérdida de bosques primarios.",
        "keywords": ["trompetero", "psophia", "trumpeter", "trompetero aliblanco"]
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
        "keywords": ["matorralero", "matorralero tricolor", "atlapetes", "tricolor", "pinzon tricolor", "motorrelero"]
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
    name_clean = class_name.lower().strip()
    
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
