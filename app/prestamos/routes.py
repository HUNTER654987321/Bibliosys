from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.decorators import rol_requerido
from app.models import Prestamo, Usuario, Libro, Devolucion, Multa, obtener_configuracion_sistema, ESTADOS_ACTIVOS_PRESTAMO

prestamos_bp = Blueprint("prestamos", __name__, url_prefix="/prestamos")

@prestamos_bp.route("/")
@login_required
def listar():
    if current_user.es_estudiante():
        prestamos = Prestamo.query.filter_by(usuario_id=current_user.id).order_by(Prestamo.id.asc()).all()
    else:
        estado = request.args.get("estado", "").strip()
        query = Prestamo.query
        if estado == "activo":
            query = query.filter(Prestamo.estado.in_(ESTADOS_ACTIVOS_PRESTAMO), Prestamo.fecha_devolucion >= date.today())
        elif estado == "vencido":
            query = query.filter(Prestamo.estado.in_(ESTADOS_ACTIVOS_PRESTAMO), Prestamo.fecha_devolucion < date.today())
        elif estado == "devuelto":
            query = query.filter_by(estado="Devuelto")
        prestamos = query.order_by(Prestamo.id.asc()).all()
    return render_template("prestamos/listar.html", prestamos=prestamos, today=date.today())

@prestamos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def nuevo():
    config = obtener_configuracion_sistema()
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre.asc()).all()
    libros = Libro.query.order_by(Libro.titulo.asc()).all()
    fecha_default = date.today() + timedelta(days=config.dias_prestamo or 7)

    if request.method == "POST":
        usuario = Usuario.query.get(request.form.get("usuario_id"))
        libro = Libro.query.get(request.form.get("libro_id"))
        fecha_devolucion_txt = request.form.get("fecha_devolucion")

        if not usuario or not usuario.activo:
            flash("Debe seleccionar un usuario activo.", "danger")
            return redirect(url_for("prestamos.nuevo"))
        if not libro:
            flash("Debe seleccionar un libro valido.", "danger")
            return redirect(url_for("prestamos.nuevo"))
        if libro.disponible <= 0:
            flash("No hay stock disponible para este libro.", "danger")
            return redirect(url_for("prestamos.nuevo"))
        try:
            fecha_devolucion = date.fromisoformat(fecha_devolucion_txt)
        except (TypeError, ValueError):
            flash("Debe ingresar una fecha de entrega valida.", "danger")
            return redirect(url_for("prestamos.nuevo"))
        if fecha_devolucion < date.today():
            flash("La fecha de entrega no puede ser anterior a hoy.", "warning")
            return redirect(url_for("prestamos.nuevo"))

        p = Prestamo(
            usuario_id=usuario.id,
            libro_id=libro.id,
            fecha_devolucion=fecha_devolucion,
            estado="Activo"
        )
        db.session.add(p)
        db.session.commit()
        flash("Prestamo registrado correctamente", "success")
        return redirect(url_for("prestamos.listar"))

    return render_template("prestamos/form.html", usuarios=usuarios, libros=libros, fecha_default=fecha_default)

@prestamos_bp.route("/devolver/<int:id>")
@login_required
@rol_requerido("Administrador", "Bibliotecario")
def devolver(id):
    p = Prestamo.query.get_or_404(id)
    if p.estado == "Devuelto":
        flash("Este prestamo ya fue devuelto", "warning")
        return redirect(url_for("prestamos.listar"))

    config = obtener_configuracion_sistema()
    p.estado = "Devuelto"
    db.session.add(Devolucion(prestamo_id=p.id, observacion="Devuelto sin observacion"))
    atraso = (date.today() - p.fecha_devolucion).days
    if atraso > 0:
        monto = atraso * (config.multa_por_dia or 2)
        db.session.add(Multa(prestamo_id=p.id, monto=monto, motivo=f"Atraso de {atraso} dia(s)"))
    db.session.commit()
    flash("Devolucion registrada correctamente", "success")
    return redirect(url_for("prestamos.listar"))

@prestamos_bp.route("/historial/<int:usuario_id>")
@login_required
def historial(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if current_user.es_estudiante() and current_user.id != usuario.id:
        flash("No tienes permiso para ver el historial de otro usuario.", "warning")
        return redirect(url_for("prestamos.listar"))
    if not current_user.tiene_rol("Administrador", "Bibliotecario", "Estudiante"):
        flash("No tienes permiso para acceder al historial.", "warning")
        return redirect(url_for("admin.dashboard"))

    prestamos = Prestamo.query.filter_by(usuario_id=usuario.id).order_by(Prestamo.id.asc()).all()
    datos = {
        "total": len(prestamos),
        "activos": sum(1 for p in prestamos if p.estado_actual == "Activo"),
        "vencidos": sum(1 for p in prestamos if p.estado_actual == "Vencido"),
        "devueltos": sum(1 for p in prestamos if p.estado_actual == "Devuelto"),
        "multas": sum((p.multa.monto if p.multa else 0) for p in prestamos)
    }
    return render_template("prestamos/historial.html", usuario=usuario, prestamos=prestamos, datos=datos, today=date.today())

@prestamos_bp.route("/mi-historial")
@login_required
def mi_historial():
    return redirect(url_for("prestamos.historial", usuario_id=current_user.id))
