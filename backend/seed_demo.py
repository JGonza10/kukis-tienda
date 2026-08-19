"""Carga productos de ejemplo para probar el catálogo.

Uso: python seed_demo.py
"""
from models import db, Producto, Variante

DEMO = [
    {
        "nombre": "Vestido floral",
        "descripcion": "Vestido ligero de algodón, estampado floral.",
        "categoria": "Vestidos",
        "precio": 350,
        "variantes": [
            {"talla": "S", "color": "Rosa", "color_hex": "#FF6FA5", "stock": 2},
            {"talla": "M", "color": "Azul", "color_hex": "#1B5FCC", "stock": 1},
        ],
    },
    {
        "nombre": "Blusa denim",
        "descripcion": "Blusa de mezclilla, corte holgado.",
        "categoria": "Blusas",
        "precio": 220,
        "variantes": [
            {"talla": "CH", "color": "Azul", "color_hex": "#1B5FCC", "stock": 3},
            {"talla": "G", "color": "Azul", "color_hex": "#1B5FCC", "stock": 1},
        ],
    },
    {
        "nombre": "Chamarra",
        "descripcion": "Chamarra ligera para entretiempo.",
        "categoria": "Abrigos",
        "precio": 480,
        "variantes": [
            {"talla": "M", "color": "Naranja", "color_hex": "#FF8A3D", "stock": 1},
        ],
    },
    {
        "nombre": "Camisa blanca",
        "descripcion": "Camisa de vestir, algodón, corte clásico.",
        "categoria": "Camisas",
        "precio": 250,
        "variantes": [
            {"talla": "38", "color": "Negro", "color_hex": "#1A1A1A", "stock": 1},
            {"talla": "40", "color": "Azul", "color_hex": "#1B5FCC", "stock": 1},
        ],
    },
    {
        "nombre": "Falda plisada",
        "descripcion": "Falda plisada a la rodilla.",
        "categoria": "Faldas",
        "precio": 280,
        "variantes": [
            {"talla": "CH", "color": "Beige", "color_hex": "#D8C3A5", "stock": 2},
            {"talla": "M", "color": "Negro", "color_hex": "#1A1A1A", "stock": 2},
        ],
    },
    {
        "nombre": "Pantalón de vestir",
        "descripcion": "Pantalón de vestir, corte recto.",
        "categoria": "Pantalones",
        "precio": 380,
        "variantes": [
            {"talla": "M", "color": "Gris", "color_hex": "#8A8A8A", "stock": 2},
            {"talla": "G", "color": "Negro", "color_hex": "#1A1A1A", "stock": 1},
        ],
    },
    {
        "nombre": "Suéter tejido",
        "descripcion": "Suéter tejido, cuello redondo.",
        "categoria": "Abrigos",
        "precio": 420,
        "variantes": [
            {"talla": "M", "color": "Vino", "color_hex": "#7A2333", "stock": 1},
        ],
    },
    {
        "nombre": "Blusa de holanes",
        "descripcion": "Blusa con holanes en las mangas.",
        "categoria": "Blusas",
        "precio": 260,
        "variantes": [
            {"talla": "CH", "color": "Blanco", "color_hex": "#FFFFFF", "stock": 2},
            {"talla": "M", "color": "Rosa", "color_hex": "#FF6FA5", "stock": 1},
        ],
    },
    {
        "nombre": "Vestido casual",
        "descripcion": "Vestido casual de tirantes, ideal para el domingo.",
        "categoria": "Vestidos",
        "precio": 310,
        "variantes": [
            {"talla": "S", "color": "Verde", "color_hex": "#3E7C4A", "stock": 1},
            {"talla": "M", "color": "Beige", "color_hex": "#D8C3A5", "stock": 2},
        ],
    },
    {
        "nombre": "Chaleco",
        "descripcion": "Chaleco acolchado, entretiempo.",
        "categoria": "Abrigos",
        "precio": 300,
        "variantes": [
            {"talla": "M", "color": "Negro", "color_hex": "#1A1A1A", "stock": 1},
            {"talla": "G", "color": "Verde", "color_hex": "#3E7C4A", "stock": 1},
        ],
    },
]


def sembrar():
    if Producto.query.first():
        print("Ya hay productos cargados, no se agregó nada.")
        return
    for item in DEMO:
        producto = Producto(
            nombre=item["nombre"],
            descripcion=item["descripcion"],
            categoria=item["categoria"],
            precio=item["precio"],
        )
        for v in item["variantes"]:
            producto.variantes.append(Variante(**v))
        db.session.add(producto)
    db.session.commit()
    print(f"Se agregaron {len(DEMO)} productos de ejemplo.")


if __name__ == "__main__":
    from app import app

    with app.app_context():
        sembrar()
