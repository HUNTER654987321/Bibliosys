from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario, Rol, Categoria, Editorial, Autor, Libro, obtener_configuracion_sistema

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        usuario = Usuario.query.filter_by(email=email, activo=True).first()
        if usuario and usuario.check_password(password):
            login_user(usuario)
            return redirect(url_for("admin.dashboard"))
        flash("Correo o contrasena incorrectos", "danger")
    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada correctamente", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/crear-admin")
def crear_admin():
    roles = ["Administrador", "Bibliotecario", "Estudiante"]
    for nombre in roles:
        if not Rol.query.filter_by(nombre=nombre).first():
            db.session.add(Rol(nombre=nombre))
    db.session.commit()

    rol_admin = Rol.query.filter_by(nombre="Administrador").first()
    admin = Usuario.query.filter_by(email="admin@biblioteca.com").first()
    if not admin:
        admin = Usuario(nombre="Administrador", email="admin@biblioteca.com", rol_id=rol_admin.id)
        admin.set_password("admin123")
        db.session.add(admin)

    rol_biblio = Rol.query.filter_by(nombre="Bibliotecario").first()
    biblio = Usuario.query.filter_by(email="bibliotecario@biblioteca.com").first()
    if not biblio:
        biblio = Usuario(nombre="Bibliotecario Demo", email="bibliotecario@biblioteca.com", rol_id=rol_biblio.id)
        biblio.set_password("123456")
        db.session.add(biblio)

    rol_est = Rol.query.filter_by(nombre="Estudiante").first()
    estudiante = Usuario.query.filter_by(email="estudiante@biblioteca.com").first()
    if not estudiante:
        estudiante = Usuario(nombre="Estudiante Demo", email="estudiante@biblioteca.com", rol_id=rol_est.id)
        estudiante.set_password("123456")
        db.session.add(estudiante)

    for nombre in ["Programacion", "Base de datos", "Redes", "Literatura", "Investigacion"]:
        if not Categoria.query.filter_by(nombre=nombre).first():
            db.session.add(Categoria(nombre=nombre, descripcion="Area de biblioteca"))
    for nombre in ["Pearson", "McGraw Hill", "Santillana"]:
        if not Editorial.query.filter_by(nombre=nombre).first():
            db.session.add(Editorial(nombre=nombre, ciudad="La Paz"))
    db.session.commit()

    if Autor.query.count() == 0:
        db.session.add_all([
            Autor(nombre="Robert Martin", nacionalidad="Estados Unidos"),
            Autor(nombre="Mario Tellez", nacionalidad="Bolivia"),
            Autor(nombre="Miguel Grinberg", nacionalidad="Estados Unidos")
        ])
        db.session.commit()

    autor1 = Autor.query.filter_by(nombre="Robert Martin").first() or Autor.query.first()
    autor2 = Autor.query.filter_by(nombre="Miguel Grinberg").first() or autor1

    if Libro.query.count() == 0:
        cat = Categoria.query.first()
        edi = Editorial.query.first()
        l1 = Libro(titulo="Clean Code", isbn="9780132350884", anio=2008, stock=4, ubicacion="A-01", categoria_id=cat.id, editorial_id=edi.id)
        l2 = Libro(titulo="Fundamentos de Flask", isbn="9780000000001", anio=2026, stock=6, ubicacion="B-02", categoria_id=cat.id, editorial_id=edi.id)
        if autor1:
            l1.autores = [autor1]
        if autor2:
            l2.autores = [autor2]
        db.session.add_all([l1, l2])
    else:
        for libro in Libro.query.all():
            if not libro.autores and autor1:
                libro.autores = [autor2 if (autor2 and "Flask" in libro.titulo) else autor1]

    obtener_configuracion_sistema()
    db.session.commit()
    return "Datos creados. Admin: admin@biblioteca.com/admin123 | Bibliotecario: bibliotecario@biblioteca.com/123456 | Estudiante: estudiante@biblioteca.com/123456"
