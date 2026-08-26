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
    
    precio_por_manzana = 1
    total = cantidad * precio_por_manzana
    
    return render_template("encargo.html", nombre=nombre, telefono=telefono, cantidad=cantidad, tipo_manzana=tipo_manzana, total=total)

# 4. Guardar en Supabase, crear PDF y redirigir a WhatsApp
@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    nombre = request.form["nombre"]
    telefono_input = request.form["telefono"]
    cantidad = request.form["cantidad"]
    tipo_manzana = request.form["tipo_manzana"]
    total = request.form["total"]
    
    # --- A. MAGIA CON EL TELÉFONO ---
    tel_limpio = telefono_input.replace("-", "").replace(" ", "")
    telefono_pdf = f"{tel_limpio[:4]}-{tel_limpio[4:]}"
    telefono_wa = f"503{tel_limpio}"
    
    # --- B. GUARDAR EN BASE DE DATOS ---
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = "INSERT INTO pedidos_manzanas (nombre, telefono, cantidad, tipo_manzana) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (nombre, tel_limpio, cantidad, tipo_manzana))
    conexion.commit()
    cursor.close()
    conexion.close()

    # --- C. CREAR EL PDF MEJORADO ---
    pdf = FPDF()
    pdf.add_page()
    
    pdf.rect(15, 15, 180, 130)
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, txt="FACTURA DE PEDIDO", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, txt="Manzanas Encarameladas", ln=True, align='C')
    pdf.ln(15)
    
    pdf.set_font("Arial", size=14)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"Cliente: {nombre}", ln=True)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"Telefono: {telefono_pdf}", ln=True)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"Producto: Manzanas tipo {tipo_manzana}", ln=True)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"Cantidad: {cantidad} unidades", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"TOTAL A PAGAR: ${total}", ln=True)
    
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, txt="¡Gracias por tu preferencia!", ln=True, align='C')

    if not os.path.exists("static/pdfs"):
        os.makedirs("static/pdfs")
        
    nombre_archivo = f"factura_{nombre.replace(' ', '_')}.pdf"
    ruta_pdf = f"static/pdfs/{nombre_archivo}"
    pdf.output(ruta_pdf)

    # --- D. GENERAR LINK DE WHATSAPP Y PANTALLA DE CARGA ---
    link_factura = f"https://tienda-python.onrender.com/{ruta_pdf}"
    mensaje = f"🍎 ¡Hola {nombre}! Tu pedido de {cantidad} manzanas ({tipo_manzana}) esta confirmado. El total es ${total}. Puedes descargar tu factura aqui: {link_factura}"
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    link_whatsapp = f"https://wa.me/{telefono_wa}?text={mensaje_codificado}"
    
    # PANTALLA DE TRANSICIÓN (Fíjate en las 3 comillas de abajo que abren)
    html_respuesta = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Guardando Pedido...</title>
    </head>
    <body style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; background-color: rgb(187, 182, 182); margin: 0;">
        <div style="background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); max-width: 500px;">
            <h2 style="color: #4a4e69; margin-bottom: 10px;">¡Pedido Guardado Exitosamente! 🍎</h2>
            <p style="color: #666; font-size: 1.1em; margin-bottom: 30px;">Abriendo WhatsApp de forma automática...</p>
            
            <div style="display: flex; justify-content: center; gap: 15px;">
                <a href="{link_whatsapp}" target="_blank" style="background: #25D366; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 0.9em;">🟢 Abrir WhatsApp Manual</a>
                <a href="/panel" style="background: #4a4e69; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 0.9em;">Volver al Panel</a>
            </div>
        </div>

        <script>
            window.open("{link_whatsapp}", "_blank");
            
            setTimeout(function() {{
                window.location.href = "/panel";
            }}, 1500);
        </script>
    </body>
    </html>
    """
    # Y fíjate en las 3 comillas de arriba que cierran
    
    return html_respuesta

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
