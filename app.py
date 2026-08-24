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

if __name__ == "__main__":
    app.run(debug=True)
