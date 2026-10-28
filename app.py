from flask import Flask, request, render_template, redirect
import psycopg2
from psycopg2.extras import RealDictCursor
from fpdf import FPDF
import urllib.parse
import os
from datetime import datetime, timedelta

app = Flask(__name__)

URL_SUPABASE = "postgresql://postgres.xethwmnjdveonvseuqgr:yRi_4G%3FzMGZLD-B@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

def conectar_bd():
    return psycopg2.connect(URL_SUPABASE)

@app.route("/")
def inicio():
    return render_template("Inicio.html")

@app.route("/panel")
def panel():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)

    # Inventario: sale de la tabla Producto
    cursor.execute('SELECT id_producto, nombre_tipo_a, precio, cantidad FROM "Producto" ORDER BY nombre_tipo_a')
    inventario = cursor.fetchall()

    # Pedidos: une Factura + Cliente + Detalle_compra
    cursor.execute('''
        SELECT f.id_factura, f.num_fac, f.fecha,
               c.nombre, c.apellido, c.correo,
               d.nombre_p, d.cantidad, d.total
        FROM "Factura" f
        JOIN "Cliente" c ON c.id_cliente = f.id_cliente
        JOIN "Detalle_compra" d ON d.id_factura = f.id_factura
        ORDER BY f.id_factura DESC
    ''')
    pedidos = cursor.fetchall()

    cursor.close()
    conexion.close()
    return render_template("panel.html", pedidos=pedidos, inventario=inventario)

@app.route("/preencargo")
def preencargo():
    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT id_producto, nombre_tipo_a, precio FROM "Producto" WHERE id_producto LIKE %s AND cantidad > 0 ORDER BY precio, nombre_tipo_a', ("A%",))
    aderezos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("preencargo.html", aderezos=aderezos)

@app.route("/procesar-pedido", methods=["POST"])
def procesar_pedido():
    nombre = request.form["nombre"].strip()
    apellido = request.form["apellido"].strip()
    correo = request.form["correo"].strip()
    cantidad = int(request.form["cantidad"])
    id_aderezo = request.form["aderezo"]

    conexion = conectar_bd()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT precio FROM "Producto" WHERE id_producto = %s', (ID_PANCAKES,))
    pancakes = cursor.fetchone()

    aderezo = None
    if id_aderezo != "ninguno":
        cursor.execute('SELECT nombre_tipo_a, precio FROM "Producto" WHERE id_producto = %s', (id_aderezo,))
        aderezo = cursor.fetchone()
    cursor.close()
    conexion.close()

    precio_pancakes = pancakes["precio"]
    precio_aderezo = aderezo["precio"] if aderezo else 0
    nombre_aderezo = aderezo["nombre_tipo_a"] if aderezo else "Sin aderezo"
    precio_unit = precio_pancakes + precio_aderezo
    total = cantidad * precio_unit

    return render_template("encargo.html",
        nombre=nombre, apellido=apellido, correo=correo, cantidad=cantidad,
        id_aderezo=id_aderezo, nombre_aderezo=nombre_aderezo,
        precio_pancakes=precio_pancakes, precio_aderezo=precio_aderezo,
        precio_unit=precio_unit, total=total)

# 4. Guardar en Supabase, crear PDF y redirigir a WhatsApp
@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    nombre = request.form["nombre"]
    telefono_input = request.form["telefono"]
    cantidad = request.form["cantidad"]
    tipo_manzana = request.form["tipo_manzana"]
    total = request.form["total"]
    
    tel_limpio = telefono_input.replace("-", "").replace(" ", "")
    telefono_pdf = f"{tel_limpio[:4]}-{tel_limpio[4:]}"
    telefono_wa = f"503{tel_limpio}"
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT stock_disponible FROM inventario_manzanas WHERE color = %s", (tipo_manzana,))
    resultado = cursor.fetchone()
    
    if not resultado:
        return "Error: El color seleccionado no existe en el inventario."
        
    stock_actual = resultado[0]
    
    if int(cantidad) > stock_actual:
        cursor.close()
        conexion.close()
        return f"""
        <div style='text-align:center; padding: 50px; font-family:Arial; background-color: rgb(187, 182, 182); height: 100vh;'>
            <div style='background: white; padding: 40px; border-radius: 20px; display: inline-block;'>
                <h2 style='color:#e63946;'>¡Uy! Stock Insuficiente</h2>
                <p>Solo nos quedan <b>{stock_actual}</b> manzanas de <b>{tipo_manzana}</b>.</p>
                <br>
                <a href='/preencargo' style='padding:10px 20px; background:#4a4e69; color:white; border-radius:10px; text-decoration:none;'>Volver al Formulario</a>
            </div>
        </div>
        """
    
    cursor.execute("UPDATE inventario_manzanas SET stock_disponible = stock_disponible - %s WHERE color = %s", (cantidad, tipo_manzana))
    
    sql_pedido = "INSERT INTO pedidos_manzanas (nombre, telefono, cantidad, tipo_manzana) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql_pedido, (nombre, tel_limpio, cantidad, tipo_manzana))
    
    conexion.commit()
    cursor.close()
    conexion.close()

    fecha_actual = (datetime.utcnow() - timedelta(hours=6)).strftime("%d/%m/%Y %H:%M")
    
    pdf = FPDF()
    pdf.add_page()
    
    pdf.rect(15, 15, 180, 140)
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, txt="TICKET DE COMPRA", ln=True, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, txt="Manzanas Encarameladas - Sistema Web", ln=True, align='C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_x(15)
    pdf.cell(175, 10, txt=f"Fecha y Hora: {fecha_actual}", ln=True, align='R')
    pdf.ln(10)
    
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

    link_factura = f"https://tienda-python.onrender.com/{ruta_pdf}"
    mensaje = f"🍎 ¡Hola {nombre}! Tu pedido de {cantidad} manzanas ({tipo_manzana}) esta confirmado. El total es ${total}. Puedes descargar tu factura aqui: {link_factura}"
    
    mensaje_codificado = urllib.parse.quote(mensaje)
    link_whatsapp = f"https://wa.me/{telefono_wa}?text={mensaje_codificado}"
    
    html_respuesta = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Pedido Guardado</title>
    </head>
    <body style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; background-color: rgb(187, 182, 182); margin: 0;">
        <div style="background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); max-width: 500px;">
            <h2 style="color: #4a4e69; margin-bottom: 10px;">¡Pedido Guardado Exitosamente!</h2>
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

@app.route("/eliminar-pedido/<int:id>", methods=["POST"])
def eliminar_pedido(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM "Detalle_compra" WHERE id_factura = %s', (id,))
    cursor.execute('DELETE FROM "V_realizadas" WHERE id_factura = %s', (id,))
    cursor.execute('DELETE FROM "Factura" WHERE id_factura = %s', (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect("/panel")

if __name__ == "__main__":
    app.run(debug=True)
