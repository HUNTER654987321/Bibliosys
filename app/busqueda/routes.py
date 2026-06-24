from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_
from app.models import Libro, Usuario, Prestamo, Categoria, Editorial, Autor

busqueda_bp = Blueprint("busqueda", __name__, url_prefix="/busqueda")

@busqueda_bp.route("/", methods=["GET"])
@login_required
def index():
    q = request.args.get("q", "").strip()
    libros = []
    usuarios = []
    prestamos = []

    if q:
        like = f"%{q}%"
        libros = Libro.query.join(Categoria).join(Editorial).filter(
            or_(
                Libro.titulo.ilike(like),
                Libro.isbn.ilike(like),
                Libro.ubicacion.ilike(like),
                Categoria.nombre.ilike(like),
                Editorial.nombre.ilike(like),
                Libro.autores.any(Autor.nombre.ilike(like))
            )
        ).order_by(Libro.titulo.asc()).limit(20).all()

        usuarios = Usuario.query.filter(
            or_(Usuario.nombre.ilike(like), Usuario.email.ilike(like))
        ).order_by(Usuario.nombre.asc()).limit(20).all()

        prestamos = Prestamo.query.join(Usuario).join(Libro).filter(
            or_(Usuario.nombre.ilike(like), Libro.titulo.ilike(like), Prestamo.estado.ilike(like))
        ).order_by(Prestamo.id.desc()).limit(20).all()

    return render_template("busqueda/index.html", q=q, libros=libros, usuarios=usuarios, prestamos=prestamos)
