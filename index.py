import os
import uuid
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from werkzeug.utils import secure_filename

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from config import Config
from models import db, Usuario, Rol, Producto, ProductoImagen


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "inicio"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
CARPETA_PRODUCTOS = os.path.join("static", "img", "productos")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def admin_required(f):
    """Decorador: solo deja pasar si el usuario logueado es admin."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/registro", methods=["POST"])
def registro():

    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip()
    password = request.form.get("password", "")
    confirmar = request.form.get("confirmar", "")

    if not nombre or not password or password != confirmar:
        return redirect(url_for("inicio"))

    if not telefono and not correo:
        return redirect(url_for("inicio"))

    existe = Usuario.query.filter(
        (Usuario.correo == correo) |
        (Usuario.telefono == telefono)
    ).first()

    if existe:
        return redirect(url_for("inicio"))

    rol_cliente = Rol.query.filter(
        db.func.lower(Rol.nombre) == "cliente"
    ).first()

    if not rol_cliente:
        return redirect(url_for("inicio"))

    nuevo_usuario = Usuario(
        nombre=nombre,
        telefono=telefono or None,
        correo=correo or None,
        rol_id=rol_cliente.id,
        activo=1
    )

    nuevo_usuario.set_password(password)

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return redirect(url_for("inicio"))

    return redirect(url_for("inicio"))


@app.route("/validar_usuario", methods=["POST"])
def validar_usuario():

    usuario_input = request.form.get("Usuario", "").strip()
    clave = request.form.get("Clave", "")

    if not usuario_input or not clave:
        return jsonify({"Respuesta": "ERROR"}), 400

    usuario = Usuario.query.filter(
        (Usuario.correo == usuario_input) |
        (Usuario.telefono == usuario_input)
    ).first()

    if not usuario:
        return jsonify({"Respuesta": "ERROR"}), 401

    if not usuario.activo:
        return jsonify({"Respuesta": "ERROR"}), 401

    if not usuario.check_password(clave):
        return jsonify({"Respuesta": "ERROR"}), 401

    if not usuario.rol:
        return jsonify({"Respuesta": "ERROR"}), 401

    login_user(usuario)

    if usuario.is_admin:
        return jsonify({"Respuesta": "OK", "redirect": "admin"})

    return jsonify({"Respuesta": "OK", "redirect": "home"})


# ---------- ADMIN ----------

@app.route("/admin")
@login_required
@admin_required
def adminHome():

    rol_cliente = Rol.query.filter(
        db.func.lower(Rol.nombre) == "cliente"
    ).first()

    total_clientes = (
        Usuario.query.filter_by(rol_id=rol_cliente.id).count()
        if rol_cliente else 0
    )

    return render_template(
        "AdminHome.html",
        usuario=current_user,
        total_productos=Producto.query.count(),
        ventas_hoy=0,
        total_clientes=total_clientes,
        total_pedidos=0
    )


@app.route("/admin/productos")
@login_required
@admin_required
def productos():

    lista_productos = Producto.query.order_by(Producto.id.desc()).all()

    return render_template(
        "productos.html",
        usuario=current_user,
        productos=lista_productos
    )


@app.route("/admin/productos/agregar", methods=["POST"])
@login_required
@admin_required
def agregar_producto():

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    precio = request.form.get("precio", "0")
    stock = request.form.get("stock", "0")
    tipo = request.form.get("tipo", "").strip()
    genero = request.form.get("genero", "").strip()
    temporada = request.form.get("temporada", "").strip()

    if not nombre:
        return redirect(url_for("productos"))

    try:
        precio = float(precio)
        stock = int(stock)
    except ValueError:
        return redirect(url_for("productos"))

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion or None,
        precio=precio,
        stock=stock,
        tipo=tipo or None,
        genero=genero or None,
        temporada=temporada or None,
        activo=True
    )

    db.session.add(nuevo_producto)
    db.session.flush()  # para tener nuevo_producto.id antes del commit

    # Carpeta física donde se guardan las imágenes
    ruta_carpeta = os.path.join(app.root_path, CARPETA_PRODUCTOS)
    os.makedirs(ruta_carpeta, exist_ok=True)

    archivos = request.files.getlist("imagenes")
    primera = True

    for archivo in archivos:

        if not archivo or archivo.filename == "":
            continue

        if not allowed_file(archivo.filename):
            continue

        extension = secure_filename(archivo.filename).rsplit(".", 1)[1].lower()
        nombre_unico = f"{uuid.uuid4().hex}.{extension}"

        archivo.save(os.path.join(ruta_carpeta, nombre_unico))

        imagen = ProductoImagen(
            producto_id=nuevo_producto.id,
            archivo=nombre_unico,
            es_principal=primera
        )
        db.session.add(imagen)
        primera = False

    db.session.commit()

    return redirect(url_for("productos"))


@app.route("/admin/productos/eliminar/<int:producto_id>", methods=["POST"])
@login_required
@admin_required
def eliminar_producto(producto_id):

    producto = Producto.query.get_or_404(producto_id)

    # Borra los archivos físicos de disco antes de borrar el registro
    ruta_carpeta = os.path.join(app.root_path, CARPETA_PRODUCTOS)

    for imagen in producto.imagenes:
        ruta_archivo = os.path.join(ruta_carpeta, imagen.archivo)
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)

    db.session.delete(producto)  # cascade borra también las filas de producto_imagenes
    db.session.commit()

    return redirect(url_for("productos"))


@app.route("/admin/categorias")
@login_required
@admin_required
def categorias():
    return "Categorías (pendiente)"


@app.route("/admin/ofertas")
@login_required
@admin_required
def ofertas():
    return "Ofertas (pendiente)"


@app.route("/admin/inventario")
@login_required
@admin_required
def inventario():
    return "Inventario (pendiente)"


@app.route("/admin/ventas")
@login_required
@admin_required
def ventas():
    return "Ventas (pendiente)"


@app.route("/admin/clientes")
@login_required
@admin_required
def clientes():
    return "Clientes (pendiente)"


@app.route("/admin/pedidos")
@login_required
@admin_required
def pedidos():
    return "Pedidos (pendiente)"


@app.route("/admin/reportes")
@login_required
@admin_required
def reportes():
    return "Reportes (pendiente)"


@app.route("/admin/configuracion")
@login_required
@admin_required
def configuracion():
    return "Configuración (pendiente)"


# ---------- CLIENTE ----------

@app.route("/home")
@login_required
def home():

    recientes = (
        Producto.query
        .filter_by(activo=True)
        .order_by(Producto.id.desc())
        .limit(8)
        .all()
    )

    return render_template("home.html", usuario=current_user, recientes=recientes)


@app.route("/catalogo")
@login_required
def catalogo():

    productos_disponibles = Producto.query.filter_by(activo=True).all()

    tipos = sorted({p.tipo for p in productos_disponibles if p.tipo})
    generos = sorted({p.genero for p in productos_disponibles if p.genero})
    temporadas = sorted({p.temporada for p in productos_disponibles if p.temporada})

    productos_por_tipo = {}
    for t in tipos:
        productos_por_tipo[t] = (
            Producto.query
            .filter_by(activo=True, tipo=t)
            .order_by(Producto.id.desc())
            .limit(6)
            .all()
        )

    return render_template(
        "catalogos.html",
        usuario=current_user,
        productos=productos_disponibles,
        productos_por_tipo=productos_por_tipo,
        tipos=tipos,
        generos=generos,
        temporadas=temporadas
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True, port=3000)