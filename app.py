from flask import Flask, request, render_template, redirect

app = Flask(__name__)

# Esta lista será nuestra "base de datos temporal"
pedidos_guardados = []

@app.route("/")
def inicio():
    return render_template("Inicio.html")

@app.route("/preencargo")
def preencargo():
    return render_template("preencargo.html")

@app.route("/procesar-pedido", methods=["POST"])
def procesar_pedido():
    nombre_cliente = request.form["nombre"]
    cantidad_manzanas = int(request.form["cantidad"])
    
    precio_por_unidad = 3
    total_a_pagar = cantidad_manzanas * precio_por_unidad
    
    return render_template("encargo.html", 
                           nombre=nombre_cliente, 
                           cantidad=cantidad_manzanas, 
                           total=total_a_pagar)

# --- NUEVAS RUTAS ---

@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    # Atrapamos los datos ocultos que nos enviará la factura
    nombre = request.form["nombre"]
    cantidad = request.form["cantidad"]
    total = request.form["total"]
    
    # Guardamos el pedido en nuestra lista de Python
    nuevo_pedido = {"nombre": nombre, "cantidad": cantidad, "total": total}
    pedidos_guardados.append(nuevo_pedido)
    
    # Redirigimos al usuario al panel de control
    return redirect("/panel")

@app.route("/panel")
def panel():
    # Mostramos la página del panel enviándole la lista de pedidos
    return render_template("panel.html", pedidos=pedidos_guardados)

    # --- RUTAS DE LA TIENDA Y PEDIDOS ---

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
    
    # Calculamos el total (Aquí asumo que cada manzana cuesta $3, puedes cambiarlo)
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
    
    # Insertamos en la tabla que acabas de crear
    sql = "INSERT INTO pedidos (nombre, cantidad, total) VALUES (%s, %s, %s)"
    cursor.execute(sql, (nombre, cantidad, total))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    # Regresamos al panel donde ya se verá el nuevo pedido
    return redirect("/panel")
if __name__ == "__main__":
    app.run(debug=True)
