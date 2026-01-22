from openai import OpenAI
from decouple import config
import json
import re
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=config("OPENAI_API_KEY"))

class ChatbotVozService:
    """
    Servicio para interpretar comandos de voz en ventas
    """
    
    @staticmethod
    def interpretar_comando_voz(texto, contexto=None):
        """
        Interpreta comando de voz del usuario
        """
        contexto = contexto or {}
        
        prompt = f"""
Eres un asistente de voz para un punto de venta. Interpreta comandos de vendedores.

CONTEXTO ACTUAL:
{json.dumps(contexto, ensure_ascii=False, indent=2)}

COMANDO DEL USUARIO: "{texto}"

Devuelve EXCLUSIVAMENTE JSON válido (sin markdown):

{{
  "accion": "agregar_cantidad | confirmar_venta | cancelar_venta | eliminar_ultimo | consultar_total | pedir_aclaracion",
  "cantidad": null o número,
  "confirmacion": true o false,
  "respuesta_chatbot": "texto natural breve"
}}

REGLAS:
1. Si menciona NÚMERO (1, 2, "tres", "cinco") → accion: "agregar_cantidad", cantidad: número
2. Si dice "sí", "ok", "confirmar", "dale" → accion: "confirmar_venta", confirmacion: true
3. Si dice "no", "cancelar" → accion: "cancelar_venta", confirmacion: false
4. Si dice "terminar venta", "finalizar", "listo" → accion: "confirmar_venta"
5. Si dice "total", "cuánto va" → accion: "consultar_total"
6. Si dice "quitar", "eliminar" → accion: "eliminar_ultimo"
7. Si no entiendes → accion: "pedir_aclaracion"

Respuesta breve (máximo 2 oraciones).
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Asistente de ventas experto en comandos de voz."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            texto_respuesta = response.choices[0].message.content
            match = re.search(r"\{.*\}", texto_respuesta, re.DOTALL)
            
            if not match:
                return {
                    'accion': 'pedir_aclaracion',
                    'cantidad': None,
                    'confirmacion': False,
                    'respuesta_chatbot': 'No entendí. ¿Puedes repetir?'
                }
            
            resultado = json.loads(match.group())
            logger.info(f"Comando interpretado: {resultado}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error interpretando comando: {e}")
            return {
                'accion': 'pedir_aclaracion',
                'cantidad': None,
                'confirmacion': False,
                'respuesta_chatbot': 'Disculpa, hubo un error.'
            }
    
    @staticmethod
    def generar_respuesta_producto_escaneado(producto_info):
        """
        Genera respuesta cuando se escanea un producto
        """
        nombre = producto_info.get('nombre', 'Producto')
        precio = producto_info.get('precio_venta', 0)
        stock = producto_info.get('stock', 0)
        
        if stock <= 0:
            return f"⚠️ {nombre} detectado, pero no hay stock disponible."
        
        return f"✅ {nombre} detectado. Precio: ${precio:.2f}. ¿Cuántos deseas agregar?"
    
    @staticmethod
    def generar_respuesta_producto_agregado(producto_info, cantidad, total_parcial):
        """
        Genera respuesta cuando se agrega producto
        """
        nombre = producto_info.get('nombre', 'Producto')
        precio = producto_info.get('precio_venta', 0)
        subtotal = precio * cantidad
        
        return (
            f"✅ {cantidad} {nombre}{'s' if cantidad > 1 else ''} agregado{'s' if cantidad > 1 else ''} "
            f"(${subtotal:.2f}). Total parcial: ${total_parcial:.2f}. "
            f"Escanea otro o di 'terminar venta'."
        )
    
    @staticmethod
    def generar_respuesta_total_venta(total, cantidad_items):
        """
        Genera respuesta del total
        """
        return (
            f"📊 Total: ${total:.2f} con {cantidad_items} "
            f"producto{'s' if cantidad_items != 1 else ''}. ¿Confirmas?"
        )