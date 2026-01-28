from openai import OpenAI
from decouple import config
import json
import re

client = OpenAI(
    api_key=config("OPENAI_API_KEY")
)

def interpretar_mensaje(mensaje):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""
Devuelve EXCLUSIVAMENTE JSON válido.
NO texto adicional.
NO markdown.

Formato exacto:
{{
  "accion": "registrar_venta | consultar_producto | productos_mas_vendidos | listar_productos | iniciar_registro_venta | pedir_aclaracion",
  "producto": null,
  "cantidad": null
}}x

Reglas IMPORTANTES:
- Si pregunta por UN producto ESPECÍFICO (ej: "stock de tijeras", "precio de cuadernos", "info de lapiceros") → consultar_producto
- Si pregunta por TODOS los productos, inventario completo o lista general → listar_productos
- Si el mensaje es SOLO "Registrar venta" SIN especificar producto → iniciar_registro_venta
- Si el mensaje incluye producto y cantidad específicos para vender → registrar_venta
- Si pregunta por productos más vendidos → productos_mas_vendidos
- Si falta información → pedir_aclaracion
- Si no se menciona cantidad → usar 1

Mensaje: "{mensaje}"
"""
        }]
    )

    texto = response.choices[0].message.content

    if not texto:
        return {"accion": "pedir_aclaracion"}

    match = re.search(r"\{.*\}", texto, re.DOTALL)

    if not match:
        return {"accion": "pedir_aclaracion"}

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"accion": "pedir_aclaracion"}