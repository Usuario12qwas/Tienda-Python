from flask import Flask, request, render_template, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from fpdf import FPDF          # NUEVO: Para crear el PDF
import urllib.parse            # NUEVO: Para crear el link de WhatsApp
import os                      # NUEVO: Para crear carpetas
from datetime import datetime

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
    
# --- B. VALIDACIÓN DE STOCK REAL EN BD ---
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    # 1. Consultar el stock actual de ese color específico
    cursor.execute("SELECT stock_disponible FROM inventario_manzanas WHERE color = %s", (tipo_manzana,))
    resultado = cursor.fetchone()
    
    if not resultado:
        return "Error: El color seleccionado no existe en el inventario."
        
    stock_actual = resultado[0]
    
    # 2. Validar si hay stock suficiente para este pedido
    if int(cantidad) > stock_actual:
        cursor.close()
        conexion.close()
        return f"""
        <div style='text-align:center; padding: 50px; font-family:Arial; background-color: rgb(187, 182, 182); height: 100vh;'>
            <div style='background: white; padding: 40px; border-radius: 20px; display: inline-block;'>
                <h2 style='color:#e63946;'>¡Uy! Stock Insuficiente 😢</h2>
                <p>Solo nos quedan <b>{stock_actual}</b> manzanas de <b>{tipo_manzana}</b>.</p>
                <br>
                <a href='/preencargo' style='padding:10px 20px; background:#4a4e69; color:white; border-radius:10px; text-decoration:none;'>Volver al Formulario</a>
            </div>
        </div>
        """
    
    # 3. Si hay stock, restamos las manzanas del inventario
    cursor.execute("UPDATE inventario_manzanas SET stock_disponible = stock_disponible - %s WHERE color = %s", (cantidad, tipo_manzana))
    
    # 4. Y finalmente guardamos el pedido
    sql_pedido = "INSERT INTO pedidos_manzanas (nombre, telefono, cantidad, tipo_manzana) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql_pedido, (nombre, tel_limpio, cantidad, tipo_manzana))
    
    conexion.commit()
    cursor.close()
    conexion.close()

# --- C. CREAR EL PDF MEJORADO (CON FECHA Y DESGLOSE) ---
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    pdf = FPDF()
    pdf.add_page()
    
    # Borde de la factura
    pdf.rect(15, 15, 180, 140)
    pdf.ln(20)
    
    # Encabezado
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, txt="TICKET DE COMPRA", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, txt="Manzanas Encarameladas - Sistema Web", ln=True, align='C')
    
    # Fecha alineada a la derecha
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, txt=f"Fecha y Hora: {fecha_actual}", ln=True, align='R')
    pdf.ln(10)
    
    # Datos del cliente y compra
    pdf.set_font("Arial", size=12)
    pdf.set_x(30)
    pdf.cell(0, 10, txt=f"Datos del Cliente:", ln=True)
    pdf.set_x(35)
    pdf.cell(0, 8, txt=f"- Nombre: {nombre}", ln=True)
    pdf.set_x(35)
    pdf.cell(0, 8, txt=f"- Telefono: {telefono_pdf}", ln=True)
    pdf.ln(5)
    
    pdf.set_x(30)
    pdf.cell(0, 10, txt=f"Desglose de la Compra:", ln=True)
    pdf.set_x(35)
    pdf.cell(0, 8, txt=f"- Producto: Manzana {tipo_manzana}", ln=True)
    pdf.set_x(35)
    pdf.cell(0, 8, txt=f"- Precio Unitario: $1.00", ln=True)
    pdf.set_x(35)
    pdf.cell(0, 8, txt=f"- Cantidad: {cantidad} unidades", ln=True)
    
    # Total
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_x(30)
    pdf.cell(0, 12, txt=f"TOTAL A PAGAR: ${cantidad}", ln=True)
    
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
    
# PANTALLA DE TRANSICIÓN SEGURA
    html_respuesta = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Pedido Guardado</title>
    </head>
    <body style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; background-color: rgb(187, 182, 182); margin: 0;">
        <div style="background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); max-width: 500px;">
            <h2 style="color: #4a4e69; margin-bottom: 10px;">¡Pedido Guardado Exitosamente! 🍎</h2>
            <p style="color: #666; font-size: 1.1em; margin-bottom: 30px;">La factura se ha creado. ¿Qué deseas hacer ahora?</p>
            
            <div style="display: flex; justify-content: center; gap: 15px;">
                <!-- Abrir WhatsApp (Se abre en otra pestaña) -->
                <a href="{link_whatsapp}" target="_blank" style="background: #25D366; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 1em;">🟢 Enviar por WhatsApp</a>
                
                <!-- Volver al panel (En la misma pestaña) -->
                <a href="/panel" style="background: #4a4e69; color: white; padding: 12px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 1em;">Volver al Panel</a>
            </div>
        </div>
    </body>
    </html>
    """
    
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
