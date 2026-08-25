from flask import Flask, request, render_template, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from fpdf import FPDF          # NUEVO: Para crear el PDF
import urllib.parse            # NUEVO: Para crear el link de WhatsApp
import os                      # NUEVO: Para crear carpetas

app = Flask(__name__)

# Puerto 6543 para la conexión gratuita
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
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]
    cantidad = int(request.form["cantidad"])
    tipo_manzana = request.form["manzana"]
    
    precio_por_manzana = 3
    total = cantidad * precio_por_manzana
    
    return render_template("encargo.html", nombre=nombre, telefono=telefono, cantidad=cantidad, tipo_manzana=tipo_manzana, total=total)

# 4. Guardar en Supabase, crear PDF y redirigir a WhatsApp
@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    # Recibimos los datos ocultos (ahora incluimos el total)
    nombre = request.form["nombre"]
    telefono = request.form["telefono"]
    cantidad = request.form["cantidad"]
    tipo_manzana = request.form["tipo_manzana"]
    total = request.form["total"]
    
    # --- A. GUARDAR EN BASE DE DATOS ---
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "INSERT INTO pedidos_manzanas (nombre, telefono, cantidad, tipo_manzana) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (nombre, telefono, cantidad, tipo_manzana))
    conexion.commit()
    cursor.close()
    conexion.close()

    # --- B. CREAR EL PDF ---
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="FACTURA DE PEDIDO", ln=True, align='C')
    pdf.ln(10)
    
    # Datos
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre}", ln=True)
    pdf.cell(200, 10, txt=f"Telefono: {telefono}", ln=True)
    pdf.cell(200, 10, txt=f"Producto: Manzanas tipo {tipo_manzana}", ln=True)
    pdf.cell(200, 10, txt=f"Cantidad: {cantidad} unidades", ln=True)
    
    # Total
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"TOTAL A PAGAR: ${total}", ln=True)

    # NUEVO: Cambiamos "facturas" por "pdfs" para que Python cree la carpeta limpia
    if not os.path.exists("static/pdfs"):
        os.makedirs("static/pdfs")
        
    # Guardar el PDF
    nombre_archivo = f"factura_{nombre.replace(' ', '_')}.pdf"
    ruta_pdf = f"static/pdfs/{nombre_archivo}"
    pdf.output(ruta_pdf)

    # --- C. GENERAR LINK DE WHATSAPP ---
    # También actualizamos el link para que coincida con "pdfs"
    link_factura = f"https://tienda-python.onrender.com/{ruta_pdf}"
    mensaje = f"🍎 ¡Hola {nombre}! Tu pedido de {cantidad} manzanas ({tipo_manzana}) esta confirmado. El total es ${total}. Puedes descargar tu factura aqui: {link_factura}"
    
    # Codificamos el texto para la URL
    mensaje_codificado = urllib.parse.quote(mensaje)
    link_whatsapp = f"https://wa.me/{telefono}?text={mensaje_codificado}"
    
    # Nos redirige a WhatsApp
    return redirect(link_whatsapp)

# 5. Eliminar un pedido
@app.route("/eliminar-pedido/<int:id>", methods=["POST"])
def eliminar_pedido(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    sql = "DELETE FROM pedidos_manzanas WHERE id = %s"
    cursor.execute(sql, (id,))
    conexion.commit()
    
    cursor.close()
    conexion.close()
    
    return redirect("/panel")

if __name__ == "__main__":
    app.run(debug=True)
