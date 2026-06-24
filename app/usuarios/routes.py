from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.decorators import rol_requerido
from app.models import Usuario, Rol

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuarios_bp.route("/")
@login_required
@rol_requerido("Administrador")
def listar():
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return render_template("usuarios/listar.html", usuarios=usuarios)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador")
def nuevo():
    roles = Rol.query.order_by(Rol.nombre.asc()).all()

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or "123456"
        rol_id = request.form.get("rol_id")
        activo = True if request.form.get("activo") == "on" else False

        if not nombre or not email or not rol_id:
            flash("Debe completar nombre, correo y rol.", "warning")
            return render_template("usuarios/form.html", roles=roles, usuario=None, accion="nuevo")

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("usuarios/form.html", roles=roles, usuario=None, accion="nuevo")

        if Usuario.query.filter_by(email=email).first():
            flash("Ya existe un usuario registrado con ese correo.", "danger")
            return render_template("usuarios/form.html", roles=roles, usuario=None, accion="nuevo")

        usuario = Usuario(nombre=nombre, email=email, rol_id=rol_id, activo=activo)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/form.html", roles=roles, usuario=None, accion="nuevo")


@usuarios_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("Administrador")
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    roles = Rol.query.order_by(Rol.nombre.asc()).all()

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        rol_id = request.form.get("rol_id")
        activo = True if request.form.get("activo") == "on" else False

        if not nombre or not email or not rol_id:
            flash("Debe completar nombre, correo y rol.", "warning")
            return render_template("usuarios/form.html", roles=roles, usuario=usuario, accion="editar")

        email_repetido = Usuario.query.filter(Usuario.email == email, Usuario.id != usuario.id).first()
        if email_repetido:
            flash("Ya existe otro usuario registrado con ese correo.", "danger")
            return render_template("usuarios/form.html", roles=roles, usuario=usuario, accion="editar")

        if password and len(password) < 6:
            flash("La nueva contraseña debe tener al menos 6 caracteres.", "warning")
            return render_template("usuarios/form.html", roles=roles, usuario=usuario, accion="editar")

        usuario.nombre = nombre
        usuario.email = email
        usuario.rol_id = rol_id
        usuario.activo = activo
        if password:
            usuario.set_password(password)

        try:
            db.session.commit()
            flash("Usuario actualizado correctamente.", "success")
            return redirect(url_for("usuarios.listar"))
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo actualizar el usuario. Verifique los datos.", "danger")

    return render_template("usuarios/form.html", roles=roles, usuario=usuario, accion="editar")


@usuarios_bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
@rol_requerido("Administrador")
def eliminar(id):
    usuario = Usuario.query.get_or_404(id)

    if usuario.id == current_user.id:
        flash("No puede eliminar su propio usuario mientras tiene la sesión iniciada.", "warning")
        return redirect(url_for("usuarios.listar"))

    if usuario.prestamos:
        usuario.activo = False
        db.session.commit()
        flash("El usuario tiene préstamos registrados. Se desactivó en lugar de eliminarse.", "warning")
        return redirect(url_for("usuarios.listar"))

    db.session.delete(usuario)
    db.session.commit()
    flash("Usuario eliminado correctamente.", "success")
    return redirect(url_for("usuarios.listar"))


@usuarios_bp.route("/<int:id>/cambiar-estado", methods=["POST"])
@login_required
@rol_requerido("Administrador")
def cambiar_estado(id):
    usuario = Usuario.query.get_or_404(id)

    if usuario.id == current_user.id:
        flash("No puede desactivar su propio usuario.", "warning")
        return redirect(url_for("usuarios.listar"))

    usuario.activo = not usuario.activo
    db.session.commit()
    flash("Estado del usuario actualizado correctamente.", "success")
    return redirect(url_for("usuarios.listar"))
