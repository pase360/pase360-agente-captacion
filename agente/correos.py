import html
from . import config as C

def E(x):
    return html.escape(str(x or ""))

def firma():
    return f"<p>{E(C.OWNER_NAME)}<br>Pase 360 · <a href=\"{E(C.WEB)}\">www.pase360.online</a></p>"

def baja():
    return '<p style="color:#777;font-size:12px">Si no querés recibir más mensajes nuestros, respondé con la palabra BAJA.</p>'

def invitacion(c):
    nombre = E(c["name"])
    if c["tipo"] == "generador":
        if c.get("subtipo") == "empresa":
            asunto = f"Un beneficio para los empleados de {c['name']}"
            sujeto, organizacion, firmante = "sus empleados", "La empresa", "quien firma por la empresa"
        else:
            asunto = f"Beneficios en comercios de Córdoba para los afiliados de {c['name']}"
            sujeto, organizacion, firmante = "sus afiliados, socios o empleados", "La organización", "quien firma por la organización"
        cuerpo = f"""<p>Hola, soy {E(C.OWNER_NAME)} de Pase 360.</p>
<p><b>¿Qué es Pase 360?</b> Es una plataforma que permite a {nombre} darles a {sujeto}
un <b>código QR</b> para obtener beneficios en comercios adheridos de Córdoba.</p>
<p><b>Cómo funciona</b></p>
<ol>
<li>{organizacion} se adhiere en pocos minutos, completa el formulario, elige el día del débito y firma el contrato.</li>
<li>Genera los QR de forma individual o masiva mediante Excel.</li>
<li>La persona presenta el QR en el comercio, que lo valida y entrega el beneficio.</li>
</ol>
<p>Cada QR se usa una sola vez y vence a fin de mes si no se usó.</p>
<p><b>Cómo se paga:</b> no hay abono fijo. Solo se pagan los QR generados; al cierre del mes se emite la factura y el cobro es por débito automático.</p>
<p><b>Para adherirse necesitan:</b> CUIT o CUIL, tarjeta para el cobro automático y nombre y DNI de {firmante}.</p>
<p><a href="{E(C.WEB_GENERADOR)}"><b>Adherirse acá</b></a>. Si tenés cualquier duda, respondé este correo.</p>"""
    else:
        asunto = f"{c['name']}: clientes nuevos con Pase 360 (6 meses gratis)"
        cuerpo = f"""<p>Hola, soy {E(C.OWNER_NAME)} de Pase 360.</p>
<p><b>¿Qué es Pase 360?</b> Es una plataforma que conecta a comercios de Córdoba con organizaciones.
Esas organizaciones entregan a sus afiliados un <b>código QR</b> para usar en los comercios adheridos.</p>
<p><b>Cómo funciona para {nombre}</b></p>
<ol>
<li>Te adherís y publicás el beneficio que quieras ofrecer.</li>
<li>La persona llega a tu local y muestra su QR.</li>
<li>Validás el QR desde la app de Pase 360 o desde tu cuenta.</li>
</ol>
<p><b>Los primeros 6 meses son gratis.</b> En el quinto mes te enviamos un resumen para que decidas si querés seguir.</p>
<p><a href="{E(C.WEB_COMERCIO)}"><b>Adherirme acá</b></a>. Si tenés cualquier duda, respondé este correo.</p>"""
    return asunto, cuerpo + firma() + baja()

def seguimiento(c, numero):
    url = C.WEB_GENERADOR if c["tipo"] == "generador" else C.WEB_COMERCIO
    if numero == 1:
        asunto = f"{c['name']}: ¿pudiste ver Pase 360?"
        cuerpo = f"""<p>Hola, te escribí hace unos días para contarte sobre Pase 360.</p>
<p>Si te interesa, podés conocer la propuesta y adherirte acá:
<a href="{E(url)}">{E(url)}</a>.</p>
<p>Si tenés alguna pregunta, respondé este correo y te contesto.</p>"""
    else:
        asunto = f"Último aviso: Pase 360 para {c['name']}"
        cuerpo = f"""<p>Hola, este es mi último mensaje para no molestarte.</p>
<p>Si Pase 360 te interesa, podés sumarte cuando quieras en
<a href="{E(url)}">{E(url)}</a>, o responderme con cualquier pregunta.</p>"""
    return asunto, cuerpo + firma() + baja()
