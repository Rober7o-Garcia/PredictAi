from openai import OpenAI
from decouple import config
import json
from apps.gameplay.models import ConocimientoNegocio
from django.utils import timezone

client = OpenAI(api_key=config("OPENAI_API_KEY"))


def extraer_conocimiento(mensaje_usuario, respuesta_bot):
    """
    Analiza la conversación y extrae conocimiento que vale la pena recordar
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Eres un extractor de conocimiento de negocio.

Tu trabajo es identificar información CLAVE que el dueño del negocio menciona y que debería recordarse permanentemente.

EXTRAE información sobre:
1. **Metas/Objetivos** - "Quiero vender $10,000 al mes", "Mi meta es crecer 20%"
2. **Preferencias** - "Mi producto estrella es X", "Prefiero enfocarme en Y"
3. **Datos Clave** - "Tengo 2 empleados", "Mi horario es lunes a viernes"
4. **Estrategias Definidas** - "Voy a hacer promoción los viernes", "Implementaré combos"
5. **Restricciones** - "No puedo invertir más de $500", "Solo vendo al por mayor"

NO EXTRAIGAS:
- Preguntas simples
- Saludos
- Consultas puntuales que no son información permanente

FORMATO DE RESPUESTA (JSON):
Si HAY información que recordar:
{
  "hay_conocimiento": true,
  "items": [
    {
      "tipo": "meta|preferencia|dato_clave|estrategia",
      "clave": "identificador_corto",  // ej: "meta_mensual", "producto_estrella"
      "valor": "el valor concreto",
      "contexto": "contexto adicional si es necesario",
      "confianza": 0.9  // 0.0 a 1.0
    }
  ]
}

Si NO hay nada importante:
{
  "hay_conocimiento": false,
  "items": []
}

EJEMPLOS:

Usuario: "Quiero vender $10,000 este mes"
{
  "hay_conocimiento": true,
  "items": [{
    "tipo": "meta",
    "clave": "meta_mensual_ingresos",
    "valor": "10000",
    "contexto": "Meta de ingresos mensuales en USD",
    "confianza": 0.95
  }]
}

Usuario: "Mi producto estrella es Harry Potter"
{
  "hay_conocimiento": true,
  "items": [{
    "tipo": "preferencia",
    "clave": "producto_estrella",
    "valor": "Harry Potter",
    "contexto": "Producto principal del negocio",
    "confianza": 0.9
  }]
}

Usuario: "¿Cuánto vendí hoy?"
{
  "hay_conocimiento": false,
  "items": []
}
"""
            },
            {
                "role": "user",
                "content": f"Usuario dijo: {mensaje_usuario}\nBot respondió: {respuesta_bot}"
            }
        ],
        temperature=0.1
    )
    
    try:
        resultado = json.loads(response.choices[0].message.content)
        return resultado
    except:
        return {"hay_conocimiento": False, "items": []}


def guardar_conocimiento(items):
    """
    Guarda el conocimiento extraído en la base de datos
    """
    guardados = []
    
    for item in items:
        conocimiento, created = ConocimientoNegocio.objects.update_or_create(
            clave=item['clave'],
            defaults={
                'tipo': item['tipo'],
                'valor': item['valor'],
                'contexto': item.get('contexto', ''),
                'confianza': item.get('confianza', 1.0),
                'activo': True
            }
        )
        guardados.append({
            'clave': item['clave'],
            'valor': item['valor'],
            'created': created
        })
    
    return guardados


def obtener_conocimiento_activo():
    """
    Recupera todo el conocimiento activo del negocio
    """
    conocimientos = ConocimientoNegocio.objects.filter(activo=True).order_by('-confianza', '-ultima_actualizacion')
    
    if not conocimientos.exists():
        return None
    
    # Formatear para el prompt del LLM
    memoria_texto = "# INFORMACIÓN CONOCIDA SOBRE ESTE NEGOCIO:\n\n"
    
    for c in conocimientos:
        memoria_texto += f"- **{c.get_tipo_display()}**: {c.clave} = {c.valor}\n"
        if c.contexto:
            memoria_texto += f"  _Contexto: {c.contexto}_\n"
    
    memoria_texto += "\n_Esta información fue mencionada por el dueño en conversaciones previas. Úsala cuando sea relevante._\n"
    
    return memoria_texto


def generar_saludo_personalizado():
    """
    Genera un saludo inicial basado en el conocimiento almacenado
    """
    conocimientos = ConocimientoNegocio.objects.filter(activo=True).order_by('-confianza')[:3]
    
    if not conocimientos.exists():
        return None
    
    # Preparar información para el saludo
    info_relevante = []
    for c in conocimientos:
        if c.tipo == 'meta':
            info_relevante.append(f"tu meta de {c.valor}")
        elif c.tipo == 'preferencia':
            info_relevante.append(f"{c.clave.replace('_', ' ')}: {c.valor}")
    
    if not info_relevante:
        return None
    
    return f"¡Hola! Recuerdo que {', '.join(info_relevante)}. ¿Cómo te ayudo hoy?"


def procesar_y_guardar_conocimiento(mensaje_usuario, respuesta_bot):
    """
    Pipeline completo: extraer, guardar y retornar resultado
    """
    resultado = extraer_conocimiento(mensaje_usuario, respuesta_bot)
    
    if resultado.get('hay_conocimiento') and resultado.get('items'):
        items_guardados = guardar_conocimiento(resultado['items'])
        return {
            'conocimiento_guardado': True,
            'items': items_guardados
        }
    
    return {
        'conocimiento_guardado': False,
        'items': []
    }