from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from app import db
from app.decorators import rol_requerido
from app.models import Categoria, Editorial, Autor

catalogos_bp = Blueprint("catalogos", __name__, url_prefix="/catalogos")


def _limpiar_texto(valor):
    return (valor or "").strip()


def _nombre_repetido(modelo, nombre, item_id=None):
    consulta = modelo.query.filter(db.func.lower(modelo.nombre) == nombre.lower())
    if item_id:
        consulta = consulta.filter(modelo.id != item_id)
    return consulta.first() is not None


@catalogos_bp.route("/")
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def index():
    categorias = Categoria.query.order_by(Categoria.nombre.asc()).all()
    editoriales = Editorial.query.order_by(Editorial.nombre.asc()).all()
    autores = Autor.query.order_by(Autor.nombre.asc()).all()
    return render_template(
        "catalogos/index.html",
        categorias=categorias,
        editoriales=editoriales,
        autores=autores,
    )


# -------------------- CATEGORIAS --------------------
@catalogos_bp.route("/categoria", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def categoria():
    nombre = _limpiar_texto(request.form.get("nombre"))
    descripcion = _limpiar_texto(request.form.get("descripcion"))

    if not nombre:
        flash("Debe ingresar el nombre de la categoría.", "warning")
        return redirect(url_for("catalogos.index"))

    if _nombre_repetido(Categoria, nombre):
        flash("Ya existe una categoría con ese nombre.", "danger")
        return redirect(url_for("catalogos.index"))

    db.session.add(Categoria(nombre=nombre, descripcion=descripcion))
    db.session.commit()
    flash("Categoría registrada correctamente.", "success")
    return redirect(url_for("catalogos.index"))


@catalogos_bp.route("/categoria/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)

    if request.method == "POST":
        nombre = _limpiar_texto(request.form.get("nombre"))
        descripcion = _limpiar_texto(request.form.get("descripcion"))

        if not nombre:
            flash("Debe ingresar el nombre de la categoría.", "warning")
            return render_template("catalogos/form_categoria.html", categoria=categoria)

        if _nombre_repetido(Categoria, nombre, categoria.id):
            flash("Ya existe otra categoría con ese nombre.", "danger")
            return render_template("catalogos/form_categoria.html", categoria=categoria)

        categoria.nombre = nombre
        categoria.descripcion = descripcion
        db.session.commit()
        flash("Categoría actualizada correctamente.", "success")
        return redirect(url_for("catalogos.index"))

    return render_template("catalogos/form_categoria.html", categoria=categoria)


@catalogos_bp.route("/categoria/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def eliminar_categoria(id):
    categoria = Categoria.query.get_or_404(id)

    if categoria.libros:
        flash("No se puede eliminar la categoría porque está asignada a uno o más libros.", "warning")
        return redirect(url_for("catalogos.index"))

    db.session.delete(categoria)
    db.session.commit()
    flash("Categoría eliminada correctamente.", "success")
    return redirect(url_for("catalogos.index"))


# -------------------- EDITORIALES --------------------
@catalogos_bp.route("/editorial", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def editorial():
    nombre = _limpiar_texto(request.form.get("nombre"))
    ciudad = _limpiar_texto(request.form.get("ciudad"))

    if not nombre:
        flash("Debe ingresar el nombre de la editorial.", "warning")
        return redirect(url_for("catalogos.index"))

    if _nombre_repetido(Editorial, nombre):
        flash("Ya existe una editorial con ese nombre.", "danger")
        return redirect(url_for("catalogos.index"))

    db.session.add(Editorial(nombre=nombre, ciudad=ciudad))
    db.session.commit()
    flash("Editorial registrada correctamente.", "success")
    return redirect(url_for("catalogos.index"))


@catalogos_bp.route("/editorial/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def editar_editorial(id):
    editorial = Editorial.query.get_or_404(id)

    if request.method == "POST":
        nombre = _limpiar_texto(request.form.get("nombre"))
        ciudad = _limpiar_texto(request.form.get("ciudad"))

        if not nombre:
            flash("Debe ingresar el nombre de la editorial.", "warning")
            return render_template("catalogos/form_editorial.html", editorial=editorial)

        if _nombre_repetido(Editorial, nombre, editorial.id):
            flash("Ya existe otra editorial con ese nombre.", "danger")
            return render_template("catalogos/form_editorial.html", editorial=editorial)

        editorial.nombre = nombre
        editorial.ciudad = ciudad
        db.session.commit()
        flash("Editorial actualizada correctamente.", "success")
        return redirect(url_for("catalogos.index"))

    return render_template("catalogos/form_editorial.html", editorial=editorial)


@catalogos_bp.route("/editorial/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def eliminar_editorial(id):
    editorial = Editorial.query.get_or_404(id)

    if editorial.libros:
        flash("No se puede eliminar la editorial porque está asignada a uno o más libros.", "warning")
        return redirect(url_for("catalogos.index"))

    db.session.delete(editorial)
    db.session.commit()
    flash("Editorial eliminada correctamente.", "success")
    return redirect(url_for("catalogos.index"))


# -------------------- AUTORES --------------------
@catalogos_bp.route("/autor", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def autor():
    nombre = _limpiar_texto(request.form.get("nombre"))
    nacionalidad = _limpiar_texto(request.form.get("nacionalidad"))

    if not nombre:
        flash("Debe ingresar el nombre del autor.", "warning")
        return redirect(url_for("catalogos.index"))

    if _nombre_repetido(Autor, nombre):
        flash("Ya existe un autor con ese nombre.", "danger")
        return redirect(url_for("catalogos.index"))

    db.session.add(Autor(nombre=nombre, nacionalidad=nacionalidad))
    db.session.commit()
    flash("Autor registrado correctamente.", "success")
    return redirect(url_for("catalogos.index"))


@catalogos_bp.route("/autor/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def editar_autor(id):
    autor = Autor.query.get_or_404(id)

    if request.method == "POST":
        nombre = _limpiar_texto(request.form.get("nombre"))
        nacionalidad = _limpiar_texto(request.form.get("nacionalidad"))

        if not nombre:
            flash("Debe ingresar el nombre del autor.", "warning")
            return render_template("catalogos/form_autor.html", autor=autor)

        if _nombre_repetido(Autor, nombre, autor.id):
            flash("Ya existe otro autor con ese nombre.", "danger")
            return render_template("catalogos/form_autor.html", autor=autor)

        autor.nombre = nombre
        autor.nacionalidad = nacionalidad
        db.session.commit()
        flash("Autor actualizado correctamente.", "success")
        return redirect(url_for("catalogos.index"))

    return render_template("catalogos/form_autor.html", autor=autor)


@catalogos_bp.route("/autor/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def eliminar_autor(id):
    autor = Autor.query.get_or_404(id)

    if autor.libros:
        flash("No se puede eliminar el autor porque está asignado a uno o más libros.", "warning")
        return redirect(url_for("catalogos.index"))

    try:
        db.session.delete(autor)
        db.session.commit()
        flash("Autor eliminado correctamente.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("No se pudo eliminar el autor porque tiene información relacionada.", "danger")

    return redirect(url_for("catalogos.index"))
