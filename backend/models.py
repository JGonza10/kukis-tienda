"""Modelos de datos de la tienda Kukis.

Un solo negocio (una vendedora), catálogo de prendas con variantes por
talla/color, imágenes por producto y apartados (reservaciones) que se
pagan y recogen en persona el domingo en el tianguis.
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def _proximo_domingo(desde=None):
    """Regresa la fecha del próximo domingo (si hoy es domingo, regresa hoy)."""
    desde = desde or datetime.utcnow()
    dias_para_domingo = (6 - desde.weekday()) % 7
    return (desde + timedelta(days=dias_para_domingo)).date()


class Usuario(db.Model):
    """La vendedora (y a futuro, quien más administre la tienda)."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(120), nullable=False, default="Vendedora")
    debe_cambiar_password = db.Column(db.Boolean, nullable=False, default=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre_usuario": self.nombre_usuario,
            "nombre": self.nombre,
            "debe_cambiar_password": self.debe_cambiar_password,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }


class Categoria(db.Model):
    """Catálogo de categorías administrable, para que el campo del producto
    sea seleccionable en vez de texto libre (evita duplicados por dedazo o
    mayúsculas, p. ej. "Blusas" vs "blusas")."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre}


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(140), nullable=False)
    descripcion = db.Column(db.Text, default="")
    categoria = db.Column(db.String(80), default="")
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    variantes = db.relationship(
        "Variante", backref="producto", cascade="all, delete-orphan", lazy=True
    )
    imagenes = db.relationship(
        "Imagen",
        backref="producto",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="Imagen.orden",
    )

    def to_dict(self, incluir_apartados=False):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "precio": float(self.precio),
            "activo": self.activo,
            "imagenes": [img.to_dict() for img in self.imagenes],
            "variantes": [v.to_dict(incluir_apartados) for v in self.variantes],
        }


class Variante(db.Model):
    """Una combinación específica de talla + color de un producto, con su stock."""

    __tablename__ = "variantes"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    talla = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(40), nullable=False)
    color_hex = db.Column(db.String(7), default="#CCCCCC")
    stock = db.Column(db.Integer, nullable=False, default=1)

    apartados = db.relationship("Apartado", backref="variante", lazy=True)

    ESTADOS_ACTIVOS = {"pendiente", "confirmado"}

    def apartados_activos(self, excluir_id=None):
        """Apartados que ya comprometieron esta prenda pero aún no se entregan ni cancelan."""
        return [
            a
            for a in self.apartados
            if a.estado in self.ESTADOS_ACTIVOS and a.id != excluir_id
        ]

    def disponible(self):
        """Lo que de verdad se le puede ofrecer a una clienta nueva ahora mismo."""
        return self.stock - len(self.apartados_activos())

    def to_dict(self, incluir_apartados=False):
        data = {
            "id": self.id,
            "producto_id": self.producto_id,
            "talla": self.talla,
            "color": self.color,
            "color_hex": self.color_hex,
            "stock": self.stock,
            "disponible": self.disponible(),
        }
        if incluir_apartados:
            data["apartados"] = [a.to_dict() for a in self.apartados]
        return data


class Imagen(db.Model):
    __tablename__ = "imagenes"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    orden = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {"id": self.id, "url": self.url, "orden": self.orden}


class Apartado(db.Model):
    """Reservación de una prenda. El pago y la entrega se hacen en persona."""

    __tablename__ = "apartados"

    id = db.Column(db.Integer, primary_key=True)
    variante_id = db.Column(db.Integer, db.ForeignKey("variantes.id"), nullable=False)
    cliente_nombre = db.Column(db.String(140), nullable=False)
    cliente_telefono = db.Column(db.String(20), nullable=False)
    notas = db.Column(db.Text, default="")
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    # pendiente | confirmado | entregado | cancelado
    fecha_apartado = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.Date, default=_proximo_domingo)

    def to_dict(self):
        producto = self.variante.producto if self.variante else None
        return {
            "id": self.id,
            "variante_id": self.variante_id,
            "producto_nombre": producto.nombre if producto else "",
            "talla": self.variante.talla if self.variante else "",
            "color": self.variante.color if self.variante else "",
            "precio": float(producto.precio) if producto else 0,
            "cliente_nombre": self.cliente_nombre,
            "cliente_telefono": self.cliente_telefono,
            "notas": self.notas,
            "estado": self.estado,
            "fecha_apartado": self.fecha_apartado.isoformat() if self.fecha_apartado else None,
            "fecha_entrega": self.fecha_entrega.isoformat() if self.fecha_entrega else None,
        }
