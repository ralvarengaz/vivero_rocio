# plantas.py
# Catálogo de plantas del Paraguay organizado por categorías

PLANTAS_PARAGUAY = {
    "Ornamentales": [
        "Santa Rita", "Jazmín paraguayo", "Flor de coco", "Clavel del aire",
        "Rosa", "Girasol", "Azucena", "Orquídea", "Geranio", "Bugambilia",
        "Dalia", "Crisantemo", "Hortensia", "Lirio", "Clavel", "Petunia",
        "Alegría del hogar", "Violeta africana", "Gladiolo", "Pensamiento",
        "Verbena", "Cala", "Margarita", "Amapola", "Flor de loto",
        "Tulipán", "Calendula", "Begonia", "Coleo", "Malvón",
        "Flor de San Juan", "Floripondio", "Agapanto", "Lavanda", "Helecho",
        "Cactus ornamental", "Suculentas", "Bromelia", "Flor de Pascua",
        "Jacarandá ornamental", "Ipomea", "Buganvilla rosada",
    ],
    "Cítricos": [
        "Naranjo", "Mandarino", "Pomelo", "Lima dulce", "Limón Tahití",
        "Limón Sutil", "Clementina", "Cidra", "Yuzu", "Kumquat",
        "Toronja", "Calamondín", "Limonero paraguayo", "Naranja agria",
        "Pomelito rosado", "Tangelo", "Mandarina Ponkan",
    ],
    "Frutales": [
        "Mango", "Guayaba", "Mamón", "Banana", "Ananá",
        "Sandía", "Melón", "Maracuyá", "Frutilla", "Carambola",
        "Aguacate", "Higuera", "Ciruela", "Durazno", "Cerezo",
        "Pera", "Manzana", "Granada", "Tuna", "Uva",
        "Guayabo del país", "Pitanga", "Araza", "Mburucuyá",
        "Ñangapiry", "Acerola", "Cajú", "Guabirá", "Ubajay",
        "Yvapovõ", "Karanda’y", "Guembé frutal",
    ],
    "Forestales": [
        "Lapacho amarillo", "Lapacho rosado", "Lapacho blanco",
        "Cedro", "Yvyra pytã", "Kurupay", "Eucalipto", "Pino Paraná",
        "Guatambú", "Urunde’y", "Tatajuba", "Yvyraro", "Incienso",
        "Timbo", "Yvyrá negra", "Guayaibi", "Quebracho blanco",
        "Quebracho colorado", "Samuhú", "Tajy morotĩ",
        "Árbol del Coral", "Laurel", "Jacarandá", "Palo rosa",
        "Guayacán", "Molle", "Pacará", "Lapachillo",
    ],
    "Medicinales": [
        "Menta’i", "Cedrón", "Burrito", "Ka’a he’ẽ", "Anís",
        "Ruda", "Manzanilla", "Poleo", "Eucalipto medicinal",
        "Romero", "Salvia", "Albahaca", "Coca paraguaya",
        "Toronjil", "Tilo", "Hierba buena", "Caña fistula",
        "Achicoria", "Ortiga", "Diente de león",
        "Carqueja", "Ñangapiry medicinal", "Iporuru",
        "Ñangapiré morotĩ", "Takuare'ẽ medicinal",
        "Paico", "Verbena medicinal", "Flor de saúco",
        "Cedrón Paraguay", "Boldo paraguayo",
    ],
}

# Generar una lista combinada de todas las plantas (útil para autocompletado)
TODAS_PLANTAS = [p for lista in PLANTAS_PARAGUAY.values() for p in lista]
