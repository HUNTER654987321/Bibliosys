from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.decorators import rol_requerido
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from app.models import Libro, Categoria, Editorial, Autor, ESTADOS_ACTIVOS_PRESTAMO

libros_bp = Blueprint("libros", __name__, url_prefix="/libros")

def _int_or_none(value):
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None

def _stock_valido(stock_value):
    try:
        stock = int(stock_value or 0)
        if stock < 0:
            return None
        return stock
    except (TypeError, ValueError):
        return None

@libros_bp.route("/")
@login_required
def listar():
    q = request.args.get("q", "").strip()
    query = Libro.query.join(Categoria).join(Editorial)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Libro.titulo.ilike(like),
            Libro.isbn.ilike(like),
            Libro.ubicacion.ilike(like),
            Categoria.nombre.ilike(like),
            Editorial.nombre.ilike(like),
            Libro.autores.any(Autor.nombre.ilike(like))
        ))
    libros = query.order_by(Libro.id.asc()).all()
    return render_template("libros/listar.html", libros=libros, q=q)

@libros_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def nuevo():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    editoriales = Editorial.query.order_by(Editorial.nombre).all()
    autores = Autor.query.order_by(Autor.nombre).all()

    if request.method == "POST":
        autor_ids = request.form.getlist("autor_ids")
        titulo = (request.form.get("titulo") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        stock = _stock_valido(request.form.get("stock") or 1)

        if not titulo or not isbn:
            flash("Debe completar titulo e ISBN.", "warning")
        elif not autor_ids:
            flash("Debe seleccionar al menos un autor.", "danger")
        elif stock is None:
            flash("El stock debe ser un numero entero igual o mayor a cero.", "danger")
        elif Libro.query.filter_by(isbn=isbn).first():
            flash("Ya existe un libro registrado con ese ISBN.", "danger")
        else:
            libro = Libro(
                titulo=titulo,
                isbn=isbn,
                anio=_int_or_none(request.form.get("anio")),
                stock=stock,
                ubicacion=(request.form.get("ubicacion") or "").strip(),
                categoria_id=request.form.get("categoria_id"),
                editorial_id=request.form.get("editorial_id")
            )
            libro.autores = Autor.query.filter(Autor.id.in_(autor_ids)).all()
            db.session.add(libro)
            db.session.commit()
            flash("Libro guardado correctamente", "success")
            return redirect(url_for("libros.listar"))

    return render_template(
        "libros/form.html",
        libro=None,
        categorias=categorias,
        editoriales=editoriales,
        autores=autores,
        selected_autores=[]
    )

@libros_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def editar(id):
    libro = Libro.query.get_or_404(id)
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    editoriales = Editorial.query.order_by(Editorial.nombre).all()
    autores = Autor.query.order_by(Autor.nombre).all()

    if request.method == "POST":
        autor_ids = request.form.getlist("autor_ids")
        titulo = (request.form.get("titulo") or "").strip()
        isbn = (request.form.get("isbn") or "").strip()
        stock = _stock_valido(request.form.get("stock") or 1)
        pendientes = libro.prestamos_pendientes

        if not titulo or not isbn:
            flash("Debe completar titulo e ISBN.", "warning")
        elif not autor_ids:
            flash("Debe seleccionar al menos un autor.", "danger")
        elif stock is None:
            flash("El stock debe ser un numero entero igual o mayor a cero.", "danger")
        elif stock < pendientes:
            flash(f"No puede colocar stock {stock}; este libro tiene {pendientes} prestamo(s) pendiente(s).", "danger")
        elif Libro.query.filter(Libro.isbn == isbn, Libro.id != libro.id).first():
            flash("Ya existe otro libro registrado con ese ISBN.", "danger")
        else:
            libro.titulo = titulo
            libro.isbn = isbn
            libro.anio = _int_or_none(request.form.get("anio"))
            libro.stock = stock
            libro.ubicacion = (request.form.get("ubicacion") or "").strip()
            libro.categoria_id = request.form.get("categoria_id")
            libro.editorial_id = request.form.get("editorial_id")
            libro.autores = Autor.query.filter(Autor.id.in_(autor_ids)).all()
            try:
                db.session.commit()
                flash("Libro actualizado correctamente", "success")
                return redirect(url_for("libros.listar"))
            except IntegrityError:
                db.session.rollback()
                flash("No se pudo actualizar el libro. Verifique los datos.", "danger")

    selected_autores = [autor.id for autor in libro.autores]
    return render_template(
        "libros/form.html",
        libro=libro,
        categorias=categorias,
        editoriales=editoriales,
        autores=autores,
        selected_autores=selected_autores
    )

@libros_bp.route("/eliminar/<int:id>")
@login_required
@rol_requerido("Administrador")
def eliminar(id):
    libro = Libro.query.get_or_404(id)
    if libro.prestamos:
        flash("No se puede eliminar el libro porque tiene prestamos en el historial.", "warning")
        return redirect(url_for("libros.listar"))
    db.session.delete(libro)
    db.session.commit()
    flash("Libro eliminado", "success")
    return redirect(url_for("libros.listar"))
