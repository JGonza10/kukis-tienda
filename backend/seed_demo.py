"""Carga productos de ejemplo para probar el catálogo localmente.

Uso: python seed_demo.py
"""
from app import app
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
]

with app.app_context():
    if Producto.query.first():
        print("Ya hay productos cargados, no se agregó nada.")
    else:
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
