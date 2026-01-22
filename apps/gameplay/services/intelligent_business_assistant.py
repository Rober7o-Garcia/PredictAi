# gameplay/services/intelligent_business_assistant.py
from openai import OpenAI
from decouple import config
import json
from .schema_generator import get_database_schema, get_sample_queries
from .sql_executor import SafeSQLExecutor

client = OpenAI(api_key=config("OPENAI_API_KEY"))

# ✅ HERRAMIENTA UNIVERSAL DE NEGOCIO
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
    Asistente enfocado SOLO en el negocio con contexto conversacional
    """
    
    # Construir mensajes con historial
    messages = [
        {
            "role": "system",
            "content": """Eres un ASISTENTE DE NEGOCIO INTELIGENTE para MIPYMEs (micro, pequeñas y medianas empresas).

TU PROPÓSITO ÚNICO:
Ayudar al dueño a tomar mejores decisiones empresariales mediante análisis de datos.

FILOSOFÍA DE TRABAJO:
- Eres un ASESOR PRÁCTICO, no un académico
- Trabajas con los datos DISPONIBLES, no esperes tener toda la información del mundo
- Das recomendaciones ACCIONABLES basadas en lo que tienes
- Si falta información ideal, das consejos con los datos actuales y sugieres qué más sería útil

CONTEXTO IMPORTANTE:
- Trabajas con CUALQUIER tipo de negocio (restaurantes, tiendas, farmacias, librerías, etc.)
- NO asumas el tipo de negocio - adáptate a los datos
- Cualquier nombre/palabra mencionada PODRÍA ser un producto del negocio
- MANTÉN CONTEXTO de la conversación - si ya hablaron de algo, recuérdalo

LO QUE HACES:
✅ Analizar ventas, inventario, rentabilidad de CUALQUIER producto/servicio
✅ Dar ESTRATEGIAS DE VENTA basadas en datos históricos y tendencias
✅ Identificar tendencias y patrones
✅ Predecir necesidades (ej: qué comprar más, cuándo hacer promociones)
✅ Calcular métricas de rendimiento
✅ Comparar períodos de tiempo
✅ Recomendar acciones CONCRETAS y PRÁCTICAS
✅ CONTINUAR conversaciones previas con contexto

CAPACIDADES ESTRATÉGICAS:
Cuando te pidan ESTRATEGIAS DE VENTA, analiza:
1. **Productos estrella** - Cuáles vender más, promocionar
2. **Productos lentos** - Estrategias para moverlos (descuentos, combos)
3. **Estacionalidad** - Cuándo aumentar/reducir stock
4. **Márgenes** - Qué productos priorizar para rentabilidad
5. **Tendencias** - Qué está creciendo, qué está bajando
6. **Pricing** - Si hay oportunidad de ajustar precios
7. **Cross-selling** - Qué productos se podrían vender juntos

IMPORTANTE - ESTRATEGIAS PRÁCTICAS:
- NO pidas información que no está en la BD (competencia, demografía, etc.)
- Trabaja con: ventas históricas, inventario, márgenes, tendencias temporales
- Da 3-5 recomendaciones CONCRETAS que el dueño pueda implementar HOY
- Sé específico: "Aumenta el stock de X en 20%" no "considera revisar inventarios"
- Incluye el "POR QUÉ" con datos

Ejemplo de BUENA estrategia:
"📊 Estrategia de Ventas para Harry Potter:

**Recomendaciones Accionables:**

1. **Aumentar Stock en 30%** 📦
   - Por qué: Vendes 15 unidades/mes, tu stock actual solo cubre 2 meses
   - Acción: Pedir 20 unidades adicionales

2. **Promoción 2x1 los Viernes** 💰
   - Por qué: El 60% de tus ventas son viernes-sábado
   - Acción: Implementar oferta temporal para aumentar volumen

3. **Bundle con Marcadores de Colores** 📚
   - Por qué: Ambos se venden a estudiantes, aumenta ticket promedio
   - Acción: Pack a $15 (ahorro de $2)
"

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

PERSONALIDAD:
- Asesor práctico y directo
- Proactivo (sugiere acciones concretas)
- Usa emojis de negocio: 📊 💰 📈 📉 💡 ⚠️ ✅ 🎯
- Hablas como un consultor de negocios, no como un robot académico

FORMATO DE RESPUESTAS:
- Si hay datos numéricos: usa tablas HTML cuando sea apropiado
- Estrategias: formato de lista numerada con acciones claras
- Si das recomendaciones: incluye el "POR QUÉ" con datos + la "ACCIÓN" específica
- Formatea montos: $X,XXX.XX (usa comas para miles)
- Sé conciso pero completo
- Prioriza ACCIONES sobre análisis teórico

FLUJO DE DECISIÓN:
1. ¿Hay contexto previo relevante? → Úsalo
2. ¿Pide estrategias/recomendaciones? → USA LA FUNCIÓN + genera recomendaciones prácticas
3. ¿La pregunta menciona un nombre/producto específico? → USA LA FUNCIÓN
4. ¿Pide análisis de ventas/inventario? → USA LA FUNCIÓN
5. ¿Es sobre métricas del negocio? → USA LA FUNCIÓN
6. ¿Es saludo o pequeña charla profesional? → Responde directamente
7. ¿Es completamente fuera de contexto Y no menciona productos? → Redirige educadamente
"""
        }
    ]
    
    # ✅ AGREGAR HISTORIAL si existe
    if historial and len(historial) > 0:
        messages.extend(historial[-10:])
    
    # Agregar el mensaje actual
    messages.append({
        "role": "user",
        "content": mensaje
    })
    
    # Primera llamada
    first_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=BUSINESS_TOOLS,
        tool_choice="auto"
    )
    
    response_message = first_response.choices[0].message
    tool_calls = response_message.tool_calls
    
    # Si NO usa herramientas → respuesta directa (saludo o redirección)
    if not tool_calls:
        return response_message.content
    
    # Si USA herramientas → es consulta/análisis de negocio
    messages.append(response_message)
    
    for tool_call in tool_calls:
        function_args = json.loads(tool_call.function.arguments)
        
        # Ejecutar análisis
        function_response = analizar_datos_negocio(
            consulta=function_args["consulta"],
            tipo_analisis=function_args["tipo_analisis"]
        )
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": "analizar_datos_negocio",
            "content": json.dumps(function_response, ensure_ascii=False)
        })
    
    # Segunda llamada: generar respuesta con análisis
    second_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    return second_response.choices[0].message.content
