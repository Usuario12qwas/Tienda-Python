from flask import Flask, request, render_template, redirect
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Cambio 1: El puerto ahora es 6543
URL_SUPABASE = "postgresql://postgres.ffozwpayyvzkrcjfhnuj:yRi_4G?zMGZLD-B@aws-0-us-east-2.pooler.supabase.com:6543/postgres"

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
    
    # Cambio 2: Traemos los datos de la nueva tabla 'pedidos_manzanas'
    cursor.execute("SELECT * FROM pedidos_manzanas ORDER BY id DESC")
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
    # Cambio 3: Recibimos TODOS los datos del formulario de preencargo
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]
    cantidad = int(request.form["cantidad"])
    tipo_manzana = request.form["manzana"] # "manzana" es el nombre en tu HTML
    
    # Calculamos el total
    precio_por_manzana = 3
    total = cantidad * precio_por_manzana
    
    # Pasamos los datos a la plantilla de la factura
    return render_template("encargo.html", nombre=nombre, telefono=telefono, cantidad=cantidad, tipo_manzana=tipo_manzana, total=total)

# 4. Guardar definitivamente en Supabase
@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    # Cambio 4: Recibimos los datos ocultos de la factura
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]
    cantidad = request.form["cantidad"]
    tipo_manzana = request.form["tipo_manzana"]
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    # Insertamos en la nueva tabla 'pedidos_manzanas'
    sql = "INSERT INTO pedidos_manzanas (nombre, telefono, cantidad, tipo_manzana) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (nombre, telefono, cantidad, tipo_manzana))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    # Regresamos al panel donde ya se verá el nuevo pedido
    return redirect("/panel")

if __name__ == "__main__":
    app.run(debug=True)
