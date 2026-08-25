from flask import Flask, request, render_template, redirect
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

URL_SUPABASE = "postgresql://postgres.ffozwpayyvzkrcjfhnuj:yRi_4G?zMGZLD-B@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def conectar_bd():
    return psycopg2.connect(URL_SUPABASE)

@app.route("/")
def inicio():
    return render_template("Inicio.html")

# 1. Ver el panel con los pedidos de la base de datos
@app.route("/panel")
def panel():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    
    # Traemos todos los pedidos ordenados del más nuevo al más viejo
    cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
    mis_pedidos = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    
    return render_template("panel.html", pedidos=mis_pedidos)

# 2. Mostrar el formulario de encargo
@app.route("/preencargo")
def preencargo():
    return render_template("preencargo.html")

# 3. Procesar los datos y mostrar la factura
@app.route("/procesar-pedido", methods=["POST"])
def procesar_pedido():
    # Recibimos los datos del formulario de preencargo
    nombre = request.form["nombre"]
    cantidad = int(request.form["cantidad"])
    
    # Calculamos el total
    precio_por_manzana = 3
    total = cantidad * precio_por_manzana
    
    # Pasamos los datos a la plantilla de la factura
    return render_template("encargo.html", nombre=nombre, cantidad=cantidad, total=total)

# 4. Guardar definitivamente en Supabase
@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    # Recibimos los datos ocultos de la factura
    nombre = request.form["nombre"]
    cantidad = request.form["cantidad"]
    total = request.form["total"]
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    # Insertamos en la tabla
    sql = "INSERT INTO pedidos (nombre, cantidad, total) VALUES (%s, %s, %s)"
    cursor.execute(sql, (nombre, cantidad, total))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    # Regresamos al panel donde ya se verá el nuevo pedido
    return redirect("/panel")

if __name__ == "__main__":
    app.run(debug=True)
