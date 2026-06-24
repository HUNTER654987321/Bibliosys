from datetime import date
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from app import db
from app.models import Usuario, Libro, Prestamo, Multa, Categoria, ESTADOS_ACTIVOS_PRESTAMO

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.es_estudiante():
        prestamos_query = Prestamo.query.filter_by(usuario_id=current_user.id)
        prestamos_lista = prestamos_query.all()
        datos = {
            "usuarios": 1,
            "libros": Libro.query.count(),
            "prestamos": prestamos_query.count(),
            "activos": sum(1 for p in prestamos_lista if p.estado_actual == "Activo"),
            "devueltos": sum(1 for p in prestamos_lista if p.estado_actual == "Devuelto"),
            "vencidos": sum(1 for p in prestamos_lista if p.estado_actual == "Vencido"),
            "multas": Multa.query.join(Prestamo).filter(Prestamo.usuario_id == current_user.id, Multa.pagado == False).count(),
            "disponibles": sum(l.disponible for l in Libro.query.all())
        }
        ultimos = prestamos_query.order_by(Prestamo.id.desc()).limit(6).all()
    else:
        prestamos_lista = Prestamo.query.all()
        datos = {
            "usuarios": Usuario.query.count(),
            "libros": Libro.query.count(),
            "prestamos": Prestamo.query.count(),
            "activos": sum(1 for p in prestamos_lista if p.estado_actual == "Activo"),
            "devueltos": sum(1 for p in prestamos_lista if p.estado_actual == "Devuelto"),
            "vencidos": sum(1 for p in prestamos_lista if p.estado_actual == "Vencido"),
            "multas": Multa.query.filter_by(pagado=False).count(),
            "disponibles": sum(l.disponible for l in Libro.query.all())
        }
        ultimos = Prestamo.query.order_by(Prestamo.id.desc()).limit(6).all()

    libros = Libro.query.order_by(Libro.id.desc()).limit(6).all()
    categorias = Categoria.query.all()
    populares = db.session.query(
        Libro,
        func.count(Prestamo.id).label("total_prestamos")
    ).join(Prestamo).group_by(Libro.id).order_by(desc("total_prestamos")).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        datos=datos,
        ultimos=ultimos,
        libros=libros,
        categorias=categorias,
        populares=populares,
        today=date.today()
    )
