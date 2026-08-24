from flask import Flask, request, render_template

app = Flask(__name__)

# 1. LA PÁGINA PRINCIPAL AHORA ES TU CATÁLOGO
@app.route("/")
def inicio():
    return render_template("Inicio.html")

# 2. EL FORMULARIO DE COMPRA
@app.route("/preencargo")
def preencargo():
    return render_template("preencargo.html")

# 3. LA CREACIÓN DE LA FACTURA
@app.route("/procesar-pedido", methods=["POST"])
def procesar_pedido():
    # Atrapamos los datos que el cliente escribió en el formulario
    nombre_cliente = request.form["nombre"]
    cantidad_manzanas = int(request.form["cantidad"])
    
    # Calculamos el precio (Ejemplo: $3 dólares/pesos por manzana)
    precio_por_unidad = 3
    total_a_pagar = cantidad_manzanas * precio_por_unidad
    
    # Enviamos la información a la factura final
    return render_template("encargo.html", 
                           nombre=nombre_cliente, 
                           cantidad=cantidad_manzanas, 
                           total=total_a_pagar)

if __name__ == "__main__":
    app.run(debug=True)
