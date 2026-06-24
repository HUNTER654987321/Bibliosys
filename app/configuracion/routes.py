from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Usuario, obtener_configuracion_sistema

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")

@configuracion_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    config = obtener_configuracion_sistema()

    if request.method == "POST":
        tipo_form = request.form.get("tipo_form")

        if tipo_form == "usuario":
            nombre = (request.form.get("nombre") or "").strip()
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            if not nombre or not email:
                flash("Debe completar nombre y correo.", "warning")
                return redirect(url_for("configuracion.index"))

            email_repetido = Usuario.query.filter(Usuario.email == email, Usuario.id != current_user.id).first()
            if email_repetido:
                flash("Ya existe otro usuario con ese correo.", "danger")
                return redirect(url_for("configuracion.index"))

            if password and len(password) < 6:
                flash("La nueva contrasena debe tener al menos 6 caracteres.", "warning")
                return redirect(url_for("configuracion.index"))

            current_user.nombre = nombre
            current_user.email = email
            if password:
                current_user.set_password(password)
            db.session.commit()
            flash("Datos del usuario actualizados correctamente", "success")
            return redirect(url_for("configuracion.index"))

        if tipo_form == "sistema":
            if not current_user.tiene_rol("Administrador", "Bibliotecario"):
                flash("No tienes permiso para modificar la configuracion del sistema.", "warning")
                return redirect(url_for("configuracion.index"))

            nombre_biblioteca = (request.form.get("nombre_biblioteca") or "").strip()
            correo = (request.form.get("correo") or "").strip().lower()
            telefono = (request.form.get("telefono") or "").strip()
            direccion = (request.form.get("direccion") or "").strip()
            try:
                dias_prestamo = int(request.form.get("dias_prestamo") or 7)
                multa_por_dia = float(request.form.get("multa_por_dia") or 2)
                if dias_prestamo <= 0 or multa_por_dia < 0:
                    raise ValueError
            except ValueError:
                flash("Los dias de prestamo y la multa deben ser valores validos.", "danger")
                return redirect(url_for("configuracion.index"))

            if not nombre_biblioteca:
                flash("Debe ingresar el nombre de la biblioteca.", "warning")
                return redirect(url_for("configuracion.index"))

            config.nombre_biblioteca = nombre_biblioteca
            config.correo = correo
            config.telefono = telefono
            config.direccion = direccion
            config.dias_prestamo = dias_prestamo
            config.multa_por_dia = multa_por_dia
            config.fecha_actualizacion = datetime.utcnow()
            db.session.commit()
            flash("Configuracion del sistema actualizada correctamente", "success")
            return redirect(url_for("configuracion.index"))

    return render_template("configuracion/index.html", config=config)
