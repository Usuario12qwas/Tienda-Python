from flask import Flask, request, render_template, session, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mi_clave_secreta_cambiar_esto"

# TU CONEXIÓN A SUPABASE
URL_SUPABASE = "postgresql://postgres:yRi_4G?zMGZLD-B@db.ffozwpayyvzkrcjfhnuj.supabase.co:5432/postgres"

def conectar_bd():
    return psycopg2.connect(URL_SUPABASE)

# REGISTRO
@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/registro", methods=["POST"])
def registro():
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]
    password = request.form["password"]

    password_hash = generate_password_hash(password)

    conexion = conectar_bd()
    cursor = conexion.cursor()

    sql = """
        INSERT INTO usuarios (nombre, telefono, password)
        VALUES (%s, %s, %s)
    """
    
    cursor.execute(sql, (nombre, telefono, password_hash))
    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect("/login")

# LOGIN
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/iniciar-sesion", methods=["POST"])
def iniciar_sesion():
    telefono = request.form["telefono"]
    password = request.form["password"]

    conexion = conectar_bd()
    # Usamos RealDictCursor para que nos devuelva los datos como un diccionario (igual que MySQL)
    cursor = conexion.cursor(cursor_factory=RealDictCursor)

    sql = "SELECT * FROM usuarios WHERE telefono = %s"
    cursor.execute(sql, (telefono,))
    usuario = cursor.fetchone()

    cursor.close()
    conexion.close()

    if usuario and check_password_hash(usuario["password"], password):
        session["usuario_id"] = usuario["id"]
        session["nombre"] = usuario["nombre"]
        return redirect("/bienvenido")

    return "Teléfono o contraseña incorrectos"

# BIENVENIDA
@app.route("/bienvenido")
def bienvenido():
    if "usuario_id" not in session:
        return redirect("/login")

    return render_template("bienvenido.html", nombre=session["nombre"])

# CERRAR SESIÓN
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)