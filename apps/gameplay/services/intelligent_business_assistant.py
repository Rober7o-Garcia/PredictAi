# gameplay/services/intelligent_business_assistant.py
from openai import OpenAI
from decouple import config
import json
from .schema_generator import get_database_schema, get_sample_queries
from .sql_executor import SafeSQLExecutor
from .memory_manager import obtener_conocimiento_activo
from apps.gameplay.models import InsightNegocio


client = OpenAI(api_key=config("OPENAI_API_KEY"))

# ✅ AGREGAR NUEVA HERRAMIENTA DE INVESTIGACIÓN
BUSINESS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analizar_datos_negocio",
            "description": """Analiza datos del negocio para responder preguntas, dar insights y recomendaciones.

USA ESTA FUNCIÓN para:
- Consultar ventas, productos, inventario
- Analizar tendencias y patrones
- Dar recomendaciones basadas en datos históricos
- Predecir necesidades de inventario
- Calcular métricas de rendimiento
- Comparar períodos de tiempo
- Identificar oportunidades de mejora

Esta función tiene acceso completo a todos los datos del negocio.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La pregunta, solicitud de análisis o recomendación del usuario"
                    },
                    "tipo_analisis": {
                        "type": "string",
                        "enum": ["consulta_simple", "analisis_comparativo", "recomendacion", "prediccion"],
                        "description": "Tipo de análisis requerido"
                    }
                },
                "required": ["consulta", "tipo_analisis"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "investigar_producto_mercado",
            "description": """Investiga información de mercado sobre un producto usando búsqueda en internet.

USA ESTA FUNCIÓN cuando el usuario pida:
- "Investiga sobre [producto]"
- "Busca información de mercado de [producto]"
- "¿Cuál es el precio de mercado de [producto]?"
- "Dame tendencias sobre [producto]"
- "¿Qué productos nuevos debería agregar?"
- "Analiza la competencia para [producto]"

Esta función busca:
- Precios de mercado y competencia
- Tendencias de demanda
- Información de popularidad
- Oportunidades de productos similares""",
            "parameters": {
                "type": "object",
                "properties": {
                    "producto": {
                        "type": "string",
                        "description": "Nombre del producto a investigar en el mercado"
                    },
                    "tipo_investigacion": {
                        "type": "string",
                        "enum": ["precio_mercado", "tendencias", "productos_similares", "analisis_completo"],
                        "description": "Qué tipo de información buscar"
                    }
                },
                "required": ["producto", "tipo_investigacion"]
            }
        }
    }
]


def analizar_datos_negocio(consulta, tipo_analisis):
    """
    Función universal que analiza datos y genera insights
    """
    
    # Prompt especializado según tipo de análisis
    if tipo_analisis == "recomendacion" or tipo_analisis == "prediccion":
        analisis_prompt = """Genera consultas SQL que permitan hacer análisis histórico y comparativo.

Para recomendaciones, considera:
- Tendencias de ventas por producto/categoría
- Estacionalidad (meses, días de la semana)
- Productos con crecimiento
- Rotación de inventario
- Márgenes de ganancia

Puedes generar MÚLTIPLES queries separadas por "|" si necesitas varios análisis."""
    else:
        analisis_prompt = """Genera la consulta SQL más apropiada para responder.

Si la consulta menciona un nombre específico de producto, usa:
- WHERE LOWER(nombre) LIKE LOWER('%nombre%')
- Esto permite encontrar productos incluso con variaciones en el nombre"""
    
    # Paso 1: Generar SQL para obtener datos
    sql_generation_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""Eres un experto en análisis de datos de negocios y SQL.

{get_database_schema()}

{get_sample_queries()}

{analisis_prompt}

REGLAS ESTRICTAS:
1. Solo SQL válido, sin explicaciones ni markdown
2. Solo SELECT (lectura)
3. Tablas con prefijo "companies_"
4. Para fechas: DATE('now'), DATE('now', '-X days'), strftime()
5. Si necesitas varios análisis, separa queries con "|"
6. Para buscar productos por nombre, usa LOWER(nombre) LIKE LOWER('%término%') para mayor flexibilidad
7. Si no se puede responder con los datos disponibles, devuelve: NO_DATA
"""
            },
            {
                "role": "user",
                "content": f"Genera SQL para: {consulta}"
            }
        ],
        temperature=0.1
    )
    
    sql_queries = sql_generation_response.choices[0].message.content.strip()
    sql_queries = sql_queries.replace('```sql', '').replace('```', '').strip()
    
    # Verificar si no hay datos disponibles
    if sql_queries == "NO_DATA":
        return {
            "success": False,
            "message": "No tengo suficiente información en la base de datos para responder esa pregunta."
        }
    
    # Ejecutar múltiples queries si es necesario
    queries_list = [q.strip() for q in sql_queries.split('|') if q.strip()]
    
    all_results = []
    for sql_query in queries_list:
        print(f"🔍 SQL Generado: {sql_query}")
        result = SafeSQLExecutor.execute_query(sql_query)
        
        if result["success"]:
            all_results.append({
                "query": sql_query,
                "data": result['data'],
                "row_count": result['row_count']
            })
        else:
            print(f"❌ Error en query: {result['error']}")
    
    # Si no hay resultados en ninguna query
    if not all_results or all(r['row_count'] == 0 for r in all_results):
        return {
            "success": False,
            "message": "No encontré información sobre eso en la base de datos del negocio.",
            "resultados": all_results  # Incluir para que el LLM pueda explicar mejor
        }
    
    return {
        "success": True,
        "tipo_analisis": tipo_analisis,
        "resultados": all_results,
        "consulta_original": consulta
    }

def asistente_negocio(mensaje, historial=None):
    """
    Asistente enfocado SOLO en el negocio con contexto conversacional Y memoria persistente
    """
    
    # CARGAR MEMORIA PERSISTENTE
    memoria_negocio = obtener_conocimiento_activo()
    
    # ✅ CARGAR INSIGHTS RECIENTES
    from apps.gameplay.models import InsightNegocio
    insights_recientes = InsightNegocio.objects.filter(activo=True).order_by('-detectado_en')[:10]
    
    insights_texto = ""
    if insights_recientes.exists():
        insights_texto = "\n\n# INSIGHTS Y PATRONES DETECTADOS AUTOMÁTICAMENTE:\n\n"
        for insight in insights_recientes:
            insights_texto += f"- [{insight.get_tipo_display()}] {insight.titulo}\n"
            insights_texto += f"  {insight.descripcion}\n"
            if insight.recomendacion:
                insights_texto += f"  💡 Recomendación: {insight.recomendacion}\n"
            insights_texto += "\n"
    
    system_prompt = """Eres un ASISTENTE DE NEGOCIO INTELIGENTE para MIPYMEs (micro, pequeñas y medianas empresas).

TU PROPÓSITO ÚNICO:
Ayudar al dueño a tomar mejores decisiones empresariales mediante análisis de datos REALES de su negocio.

REGLA DE ORO - SIEMPRE USA DATOS REALES:
🚨 NUNCA des ejemplos hipotéticos o teóricos
🚨 SIEMPRE consulta la base de datos primero
🚨 Si el usuario pregunta por datos específicos, USA LA FUNCIÓN antes de responder

FILOSOFÍA DE TRABAJO:
- Eres un ASESOR PRÁCTICO que trabaja con DATOS REALES
- NO des ejemplos genéricos - consulta la BD y responde con cifras exactas
- Si el usuario pregunta "¿cuánto cuesta X?", "¿cuál es mi margen de Y?", "¿cuánto vendí?" → USA analizar_datos_negocio INMEDIATAMENTE

CONTEXTO IMPORTANTE:
- Trabajas con CUALQUIER tipo de negocio (restaurantes, tiendas, farmacias, librerías, etc.)
- NO asumas el tipo de negocio - adáptate a los datos
- Cualquier nombre/palabra mencionada PODRÍA ser un producto del negocio
- MANTÉN CONTEXTO de la conversación - si ya hablaron de algo, recuérdalo
- TIENES MEMORIA PERSISTENTE - Información que el dueño mencionó antes
- PUEDES INVESTIGAR EL MERCADO - Usa la función de investigación cuando sea útil

LO QUE HACES:
✅ Analizar ventas, inventario, rentabilidad de CUALQUIER producto/servicio
✅ Dar ESTRATEGIAS DE VENTA basadas en datos históricos y tendencias
✅ INVESTIGAR INFORMACIÓN DE MERCADO sobre productos
✅ Comparar precios con el mercado
✅ Identificar tendencias y patrones
✅ Calcular márgenes de ganancia REALES (no ejemplos)
✅ Predecir necesidades (ej: qué comprar más, cuándo hacer promociones)
✅ Calcular métricas de rendimiento
✅ Comparar períodos de tiempo
✅ Recomendar acciones CONCRETAS y PRÁCTICAS
✅ CONTINUAR conversaciones previas con contexto
✅ RECORDAR información importante entre conversaciones

CUANDO USAR LAS FUNCIONES (MUY IMPORTANTE):
📊 **analizar_datos_negocio** - USA ESTA FUNCIÓN SIEMPRE para:
   - "¿Cuánto cuesta X?"
   - "¿Cuál es el precio de Y?"
   - "¿Cuánto vendí [período]?"
   - "¿Qué productos tengo?"
   - "¿Cuál es mi margen de X?"
   - "Dame info de [producto]"
   - "¿Stock de X?"
   - CUALQUIER pregunta sobre datos específicos del negocio

🔍 **investigar_producto_mercado** - USA cuando:
   - "Investiga sobre [producto]"
   - "Precio de mercado de X"
   - "Tendencias de X"
   - "¿Qué productos nuevos agregar?"

IMPORTANTE - NUNCA DES EJEMPLOS HIPOTÉTICOS:
❌ MAL: "Por ejemplo, supongamos que te costó $0.80..."
✅ BIEN: [Usa función] "Tu Cuaderno Espiral A4 te cuesta $0.80 y lo vendes a $1.50..."

Si el usuario pregunta por UN producto específico que mencionó antes o que está en contexto:
1. USA analizar_datos_negocio INMEDIATAMENTE
2. NO pidas aclaraciones innecesarias si está claro del contexto
3. Responde con los datos REALES

CAPACIDADES ESTRATÉGICAS:
Cuando te pidan ESTRATEGIAS DE VENTA, analiza:
1. **Productos estrella** - Cuáles vender más, promocionar
2. **Productos lentos** - Estrategias para moverlos (descuentos, combos)
3. **Estacionalidad** - Cuándo aumentar/reducir stock
4. **Márgenes** - Qué productos priorizar para rentabilidad
5. **Tendencias** - Qué está creciendo, qué está bajando
6. **Pricing** - Si hay oportunidad de ajustar precios (investiga mercado si es necesario)
7. **Cross-selling** - Qué productos se podrían vender juntos

IMPORTANTE - ESTRATEGIAS PRÁCTICAS:
- Primero analiza datos internos con analizar_datos_negocio
- Si necesitas contexto de mercado, USA investigar_producto_mercado
- Da 3-5 recomendaciones CONCRETAS que el dueño pueda implementar HOY
- Sé específico: "Aumenta el stock de X en 20%" no "considera revisar inventarios"
- Incluye el "POR QUÉ" con datos

REGLA CRÍTICA - CONTEXTO CONVERSACIONAL:
- Si el usuario dice "sí", "dame más info", "quiero análisis profundo", "cuéntame más", etc. → Revisa el historial para saber de QUÉ están hablando
- Si mencionaron un producto antes → Asume que se refieren a ESE producto
- Mantén coherencia con la conversación previa

REGLA CRÍTICA - VERIFICACIÓN DE PRODUCTOS:
- Si mencionan un NOMBRE específico, asume que podría ser un PRODUCTO del negocio
- SIEMPRE usa la función para verificar si existe en la base de datos
- Solo después de verificar que NO existe como producto, puedes redirigir educadamente

LO QUE NO HACES:
❌ NO hablas de clima, deportes genéricos, noticias políticas
❌ NO cuentas chistes ni entretenimiento general
❌ NO das información completamente fuera del contexto empresarial
❌ NO pides datos que no están disponibles en la BD
❌ NO des respuestas genéricas tipo "considera revisar" - sé ESPECÍFICO
❌ NO des ejemplos hipotéticos - SIEMPRE usa datos reales

PERSONALIDAD:
- Asesor práctico y directo
- Proactivo (sugiere acciones concretas)
- Usa emojis de negocio: 📊 💰 📈 📉 💡 ⚠️ ✅ 🎯 🔍
- Hablas como un consultor de negocios con acceso a DATOS REALES

FORMATO DE RESPUESTAS:
- Si hay datos numéricos: usa tablas HTML cuando sea apropiado
- Estrategias: formato de lista numerada con acciones claras
- Si investigaste el mercado: presenta hallazgos de forma clara
- Si das recomendaciones: incluye el "POR QUÉ" con datos + la "ACCIÓN" específica
- Formatea montos: $X,XXX.XX (usa comas para miles)
- Usa markdown para formato (**, ###, listas, etc.)
- Sé conciso pero completo
- Prioriza ACCIONES sobre análisis teórico
- Para fórmulas matemáticas: usa LaTeX con delimitadores \\[ ... \\] para fórmulas en bloque
- Para fórmulas inline: usa \\( ... \\)
- Ejemplo de fórmula en bloque:
  [
  text{Margen} = \\frac{\\text{Precio Venta} - \\text{Costo}}{\\text{Precio Venta}} \\times 100
  ]
- Estrategias: formato de lista numerada con acciones claras

FLUJO DE DECISIÓN:
1. ¿Hay información en la memoria persistente relevante? → Úsala
2. ¿Hay contexto previo relevante en esta conversación? → Úsalo
3. ¿El usuario pregunta por DATOS ESPECÍFICOS del negocio? → USA analizar_datos_negocio INMEDIATAMENTE
4. ¿Pide estrategias/recomendaciones? → USA analizar_datos_negocio + genera recomendaciones prácticas
5. ¿La pregunta menciona un nombre/producto específico? → USA analizar_datos_negocio
6. ¿Pide investigación de mercado? → USA investigar_producto_mercado
7. ¿Es saludo o pequeña charla profesional? → Responde directamente (usa memoria si es relevante)
8. ¿Es completamente fuera de contexto Y no menciona productos? → Redirige educadamente
"""
    
    # AGREGAR MEMORIA AL PROMPT SI EXISTE
    if memoria_negocio:
        system_prompt += f"\n\n{memoria_negocio}"
    
    if insights_texto:
        system_prompt += insights_texto
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # AGREGAR HISTORIAL si existe
    if historial and len(historial) > 0:
        messages.extend(historial[-10:])
    
    # Agregar el mensaje actual
    messages.append({"role": "user", "content": mensaje})
    
    # Primera llamada
    first_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=BUSINESS_TOOLS,
        tool_choice="auto"
    )
    
    response_message = first_response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Si NO usa herramientas → respuesta directa
    if not tool_calls:
        return response_message.content
    
    # Si USA herramientas → ejecutarlas
    messages.append(response_message)
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Ejecutar la función apropiada
        if function_name == "analizar_datos_negocio":
            function_response = analizar_datos_negocio(
                consulta=function_args["consulta"],
                tipo_analisis=function_args["tipo_analisis"]
            )
        elif function_name == "investigar_producto_mercado":
            function_response = investigar_producto_mercado(
                producto=function_args["producto"],
                tipo_investigacion=function_args["tipo_investigacion"]
            )
        else:
            function_response = {"error": "Función no reconocida"}
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(function_response, ensure_ascii=False)
        })
    
    # Segunda llamada: generar respuesta con análisis
    second_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    return second_response.choices[0].message.content