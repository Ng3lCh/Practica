from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    usuarios = db.relationship("Usuario", backref="rol", lazy=True)


class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=True)
    correo = db.Column(db.String(150), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, default=2)
    fecha_registro = db.Column(db.TIMESTAMP, server_default=db.func.now())
    activo = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        # "in" en vez de "==" para tolerar "Admin", "Administrador", etc.
        return self.rol is not None and "admin" in self.rol.nombre.strip().lower()


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    tipo = db.Column(db.String(30), nullable=True)
    genero = db.Column(db.String(20), nullable=True)
    temporada = db.Column(db.String(20), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.TIMESTAMP, server_default=db.func.now())

    imagenes = db.relationship(
        "ProductoImagen",
        backref="producto",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def imagen_principal(self):
        if not self.imagenes:
            return None
        for img in self.imagenes:
            if img.es_principal:
                return img
        return self.imagenes[0]


class ProductoImagen(db.Model):
    __tablename__ = "producto_imagenes"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    archivo = db.Column(db.String(255), nullable=False)
    es_principal = db.Column(db.Boolean, default=False)