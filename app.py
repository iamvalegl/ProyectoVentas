from flask import Flask, render_template,request, redirect,session,make_response
from config.conexion import conexion
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
app.secret_key='miclave'

def mostrarTodo():
    cursor=conexion.cursor()
    sql="select * from tbcliente"
    cursor.execute(sql)
    datos=cursor.fetchall()
    return datos

def mostrarCliente(id):
    cursor=conexion.cursor()    
    
    sql="select * from tbcliente where id_cliente=%s"
    cursor.execute(sql,(id,))
    datos=cursor.fetchone()
    return datos

@app.route('/')
def index():
    if 'usuario' in session:
        mostrar=mostrarTodo()
        return render_template("formulario.html",mostrar=mostrar)
    return render_template("login.html")

@app.route('/registro', methods=['post','get'])
def registro():
    nombre=request.form['txtnombre']
    nit=request.form['txtnit']
    cursor=conexion.cursor()
    sql="INSERT INTO tbcliente (nombre,nit) values(%s,%s)"
    cursor.execute(sql,(nombre,nit))
    conexion.commit()
    cursor.close
    mostrar=mostrarTodo()
    return render_template('formulario.html',mostrar=mostrar)

@app.route('/actualizar_cliente', methods=['post','get'])
def actualizar_cliente():
    id=request.form['txtid']
    nombre=request.form['txtnombre']
    nit=request.form['txtnit']
    cursor=conexion.cursor()
    sql="UPDATE tbcliente set nombre=%s, nit=%s where id_cliente=%s"
    cursor.execute(sql,(nombre,nit,id))
    conexion.commit()
    cursor.close
    return redirect('/')

@app.route('/actualizar/<id>')
def actualizar(id):
    cursor=conexion.cursor()
    sql="select * from tbcliente where id_cliente=%s"
    cursor.execute(sql,(id,))
    dato=cursor.fetchone()
    cursor.close
    return render_template('actualizar.html',dato=dato)

@app.route('/eliminar/<id>')
def eliminar(id):
    cursor=conexion.cursor()
    sql="delete  from tbcliente where id_cliente=%s"
    cursor.execute(sql,(id,))
    conexion.commit()
    cursor.close
    return redirect('/')

@app.route('/comprar/<id>')
def comprar(id):
    datos=mostrarCliente(id)
    return render_template('comprar.html',id=id,datos=datos)


@app.route('/comprar', methods=['post'])
def insertarComprar():
    id=request.form['txtid']
    producto=request.form['txtproducto']
    cantidad=request.form['txtcantidad']
    costo=request.form['txtcosto']

    cursor=conexion.cursor()
    sql="INSERT INTO tbcompra (tbcliente_id_cliente, producto, cantidad, costo) values(%s,%s,%s,%s)"
    cursor.execute(sql,(id,producto,cantidad,costo))
    conexion.commit()
    cursor.close
    return redirect('/')

@app.route('/vercompras/<id>', methods=['GET'])
def vercompras(id):
   cursor=conexion.cursor()
   sql="Select * from tbcompra where tbcliente_id_cliente=%s"
   cursor.execute(sql,(id,))
   datos=cursor.fetchall()
   return render_template('vercompras.html',datos=datos)

@app.route('/buscar', methods=['GET'])
def buscar():
    cursor=conexion.cursor()
    buscar=request.args.get('txtbuscar')
    sql="Select * from tbcliente where nombre like %s"
    cursor.execute(sql,(buscar+'%',))
    mostrar=cursor.fetchall()
    return render_template('formulario.html',mostrar=mostrar)

@app.route('/login', methods=['GET','POST'])
def login():
    mensaje=''
    if request.method=='POST':
        user=request.form['txtuser']
        clave=request.form['txtclave']

        cursor=conexion.cursor()
        sql="Select * from tbusuario where user=%s"
        cursor.execute(sql,(user,))
        usuario=cursor.fetchone()
        cursor.close()

        if usuario and check_password_hash(usuario[2], clave):
            session['usuario']=usuario[1]
            session['clave']=usuario[2]
            return redirect('/')
        else:
            mensaje="Usuario o contraseña incorrecto"
    return render_template('login.html',mensaje=mensaje)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/reporte/<id>')
def generar_pdf(id):
    cursor = conexion.cursor()

    sql = """
    SELECT c.nombre, c.nit, co.producto, co.cantidad, co.costo
    FROM tbcompra co
    INNER JOIN tbcliente c ON co.tbcliente_id_cliente = c.id_cliente
    WHERE co.tbcliente_id_cliente = %s
    """
    cursor.execute(sql, (id,))
    datos = cursor.fetchall()
    cursor.close()

    if not datos:
        return "No se encontraron compras para este cliente", 404

    nombre_cliente = datos[0][0]  # El nombre viene en la primera columna
    nit_cliente = datos[0][1]  # El NIT viene en la 

# Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="REPORTE DE COMPRAS", ln=True, align="C")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Cliente: {nombre_cliente}", ln=True)
    pdf.cell(200, 5, txt=f"NIT: {nit_cliente}", ln=True)
    pdf.ln(5)

    # Cabecera de la tabla
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "Producto", 1)
    pdf.cell(30, 10, "Cantidad", 1)
    pdf.cell(30, 10, "Costo", 1)
    pdf.cell(40, 10, "Total", 1)
    pdf.ln()

    # Datos
    pdf.set_font("Arial", '', 10)
    for fila in datos:
        _, _, producto, cantidad, costo = fila
        total = float(cantidad) * float(costo)
        pdf.cell(60, 10, str(producto), 1)
        pdf.cell(30, 10, str(cantidad), 1)
        pdf.cell(30, 10, f"{costo:.2f}", 1)
        pdf.cell(40, 10, f"{total:.2f}", 1)
        pdf.ln()

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte_compras.pdf'
    return response

@app.route('/usuarios')
def usuarios():
    return render_template('usuarios.html')

@app.route('/insertar_usuario', methods=['POST'])
def insertar_usuario():
    user=request.form['txtuser']
    clave=request.form['txtclave']
    rol=request.form['txtrol']
    claveRepetir=request.form['txtclaveRepetir']
    clave_hash=generate_password_hash(clave)
    
    if clave==claveRepetir:
        cursor=conexion.cursor()
        sql="INSERT INTO tbusuario (user, clave, rol) values(%s,%s,%s)"
        cursor.execute(sql,(user,clave_hash,rol))
        conexion.commit()
        cursor.close()
    else: 
        return render_template('usuarios.html',mensaje="Las contraseñas no coinciden")
    
    return redirect('/logout')

if __name__=='__main__':
    app.run(debug=True)