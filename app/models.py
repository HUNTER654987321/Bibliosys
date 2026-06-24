from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

ESTADOS_ACTIVOS_PRESTAMO = ("Activo", "Vencido", "Prestado")

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

libro_autor = db.Table(
    "libro_autor",
    db.Column("libro_id", db.Integer, db.ForeignKey("libros.id"), primary_key=True),
    db.Column("autor_id", db.Integer, db.ForeignKey("autores.id"), primary_key=True)
)

class Rol(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    usuarios = db.relationship("Usuario", backref="rol", lazy=True)

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    prestamos = db.relationship("Prestamo", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def es_admin(self):
        return self.rol and self.rol.nombre == "Administrador"

    def es_bibliotecario(self):
        return self.rol and self.rol.nombre == "Bibliotecario"

    def es_estudiante(self):
        return self.rol and self.rol.nombre == "Estudiante"

    def tiene_rol(self, *roles):
        return self.rol and self.rol.nombre in roles

class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    libros = db.relationship("Libro", backref="categoria", lazy=True)

class Editorial(db.Model):
    __tablename__ = "editoriales"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    ciudad = db.Column(db.String(80))
    libros = db.relationship("Libro", backref="editorial", lazy=True)

class Autor(db.Model):
    __tablename__ = "autores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), unique=True, nullable=False)
    nacionalidad = db.Column(db.String(80))
    libros = db.relationship("Libro", secondary=libro_autor, back_populates="autores")

class Libro(db.Model):
    __tablename__ = "libros"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(180), nullable=False)
    isbn = db.Column(db.String(30), unique=True, nullable=False)
    anio = db.Column(db.Integer)
    stock = db.Column(db.Integer, default=1)
    ubicacion = db.Column(db.String(80))
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    editorial_id = db.Column(db.Integer, db.ForeignKey("editoriales.id"), nullable=False)
    autores = db.relationship("Autor", secondary=libro_autor, back_populates="libros")
    prestamos = db.relationship("Prestamo", backref="libro", lazy=True)

    @property
    def prestamos_pendientes(self):
        return sum(1 for p in self.prestamos if p.estado in ESTADOS_ACTIVOS_PRESTAMO and p.estado_actual != "Devuelto")

    @property
    def disponible(self):
        return max((self.stock or 0) - self.prestamos_pendientes, 0)

class Prestamo(db.Model):
    __tablename__ = "prestamos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey("libros.id"), nullable=False)
    fecha_prestamo = db.Column(db.Date, default=date.today)
    fecha_devolucion = db.Column(db.Date, default=lambda: date.today() + timedelta(days=7))
    estado = db.Column(db.String(30), default="Activo")
    devolucion = db.relationship("Devolucion", backref="prestamo", uselist=False)
    multa = db.relationship("Multa", backref="prestamo", uselist=False)

    @property
    def estado_actual(self):
        if self.estado == "Devuelto":
            return "Devuelto"
        if self.fecha_devolucion and self.fecha_devolucion < date.today():
            return "Vencido"
        return "Activo"

    @property
    def clase_estado(self):
        estado = self.estado_actual
        if estado == "Devuelto":
            return "badge-ok"
        if estado == "Vencido":
            return "badge-danger-soft"
        return "badge-warn"

class Devolucion(db.Model):
    __tablename__ = "devoluciones"
    id = db.Column(db.Integer, primary_key=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey("prestamos.id"), nullable=False)
    fecha_real = db.Column(db.Date, default=date.today)
    observacion = db.Column(db.String(255))

class Multa(db.Model):
    __tablename__ = "multas"
    id = db.Column(db.Integer, primary_key=True)
    prestamo_id = db.Column(db.Integer, db.ForeignKey("prestamos.id"), nullable=False)
    monto = db.Column(db.Float, default=0)
    motivo = db.Column(db.String(255))
    pagado = db.Column(db.Boolean, default=False)

class SistemaConfig(db.Model):
    __tablename__ = "sistema_config"
    id = db.Column(db.Integer, primary_key=True)
    nombre_biblioteca = db.Column(db.String(120), default="BiblioSys")
    correo = db.Column(db.String(120), default="biblioteca@demo.com")
    telefono = db.Column(db.String(30), default="")
    direccion = db.Column(db.String(180), default="")
    dias_prestamo = db.Column(db.Integer, default=7)
    multa_por_dia = db.Column(db.Float, default=2.0)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def obtener_configuracion_sistema():
    config = SistemaConfig.query.first()
    if not config:
        config = SistemaConfig()
        db.session.add(config)
        db.session.commit()
    return config
