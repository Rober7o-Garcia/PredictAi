from apps.companies.models import Producto, Venta, ItemVenta
from django.db.models import Sum, Q
from decimal import Decimal
from rapidfuzz import fuzz, process

def buscar_producto_inteligente(nombre_busqueda, umbral=60):
    """
    Búsqueda inteligente multicapa con autocompletado
    Retorna: (producto, es_exacto, similitud, sugerencias)
    """
    if not nombre_busqueda:
        return None, False, 0, []
    
    nombre_limpio = nombre_busqueda.strip().lower()
    productos = Producto.objects.filter(activo=True)
    
    if not productos.exists():
        return None, False, 0, []
    
    # ✅ CAPA 1: Búsqueda exacta
    producto_exacto = productos.filter(nombre__iexact=nombre_busqueda).first()
    if producto_exacto:
        return producto_exacto, True, 100, []
    
    # ✅ CAPA 2: Empieza con... (mayor prioridad)
    productos_comienzan = productos.filter(nombre__istartswith=nombre_busqueda)
    if productos_comienzan.count() == 1:
        return productos_comienzan.first(), False, 95, []
    elif productos_comienzan.count() > 1:
        # Múltiples coincidencias - devolver sugerencias
        sugerencias = [p.nombre for p in productos_comienzan[:5]]
        return None, False, 90, sugerencias
    
    # ✅ CAPA 3: Contiene todas las palabras clave
    palabras = nombre_limpio.split()
    if len(palabras) >= 2:
        # Buscar productos que contengan TODAS las palabras
        q_objects = Q()
        for palabra in palabras:
            if len(palabra) > 2:  # Ignorar palabras muy cortas
                q_objects &= Q(nombre__icontains=palabra)
        
        productos_palabras = productos.filter(q_objects)
        if productos_palabras.count() == 1:
            return productos_palabras.first(), False, 85, []
        elif productos_palabras.count() > 1:
            sugerencias = [p.nombre for p in productos_palabras[:5]]
            return None, False, 80, sugerencias
    
    # ✅ CAPA 4: Contiene la frase (parcial)
    productos_contienen = productos.filter(nombre__icontains=nombre_busqueda)
    if productos_contienen.count() == 1:
        return productos_contienen.first(), False, 75, []
    elif productos_contienen.count() > 1:
        sugerencias = [p.nombre for p in productos_contienen[:5]]
        return None, False, 70, sugerencias
    
    # ✅ CAPA 5: Fuzzy matching (última opción)
    nombres_productos = {p.nombre: p for p in productos}
    resultado = process.extractOne(
        nombre_busqueda,
        nombres_productos.keys(),
        scorer=fuzz.token_sort_ratio
    )
    
    if resultado and resultado[1] >= umbral:
        nombre_match, similitud, _ = resultado
        return nombres_productos[nombre_match], False, similitud, []
    
    # ❌ No se encontró nada - intentar sugerencias generales
    resultados_fuzzy = process.extract(
        nombre_busqueda,
        nombres_productos.keys(),
        scorer=fuzz.token_sort_ratio,
        limit=5
    )
    
    sugerencias = [r[0] for r in resultados_fuzzy if r[1] >= 40]
    
    return None, False, 0, sugerencias


def ejecutar_accion(data):
    accion = data.get("accion")

    # 🆕 INICIAR FLUJO DE REGISTRO
    if accion == "iniciar_registro_venta":
        return (
            "📝 Perfecto, vamos a registrar una venta.\n\n"
            "¿Qué producto vendiste y cuántas unidades?\n\n"
            "Ejemplo: 'Vendí 3 cuadernos' o '2 lapiceros a $0.50'"
        )

    # 🛒 REGISTRAR VENTA
    if accion == "registrar_venta":
        nombre_producto = data.get("producto", "")
        producto, es_exacto, similitud, sugerencias = buscar_producto_inteligente(nombre_producto)

        # Si hay múltiples sugerencias, mostrarlas
        if not producto and sugerencias:
            respuesta = f"🔍 Encontré varios productos similares a '{nombre_producto}':\n\n"
            for i, sugerencia in enumerate(sugerencias, 1):
                respuesta += f"{i}. {sugerencia}\n"
            respuesta += "\n💡 Por favor, especifica cuál producto quieres registrar."
            return respuesta

        if not producto:
            return f"❌ No encontré ningún producto similar a '{nombre_producto}'"

        cantidad = data.get("cantidad", 1)

        if producto.stock_actual < cantidad:
            return (
                f"⚠️ Stock insuficiente de {producto.nombre}.\n"
                f"Disponible: {producto.stock_actual}"
            )

        # ✅ Crear la venta
        venta = Venta.objects.create()
        
        ItemVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
            costo_unitario=producto.precio_compra
        )
        
        venta.calcular_total()
        
        producto.stock_actual -= cantidad
        producto.save()

        respuesta = f"✅ Venta registrada por ${venta.total}\n"
        respuesta += f"📦 Stock actual de {producto.nombre}: {producto.stock_actual}"
        
        if not es_exacto and similitud < 100:
            respuesta += f"\n\n💡 (Encontré: {producto.nombre})"
        
        return respuesta

    # 📦 CONSULTAR UN PRODUCTO ESPECÍFICO
    if accion == "consultar_producto":
        nombre_producto = data.get("producto", "")
        producto, es_exacto, similitud, sugerencias = buscar_producto_inteligente(nombre_producto)

        # Si hay múltiples sugerencias, mostrarlas
        if not producto and sugerencias:
            respuesta = f"🔍 Encontré varios productos similares a '{nombre_producto}':\n\n"
            respuesta += "<ul style='margin:8px 0; padding-left:20px;'>"
            for sugerencia in sugerencias:
                respuesta += f"<li>{sugerencia}</li>"
            respuesta += "</ul>"
            respuesta += "<em>💡 Por favor, especifica cuál producto quieres consultar.</em>"
            return respuesta

        if not producto:
            return f"❌ No encontré ningún producto similar a '{nombre_producto}'"

        # Calcular total vendido
        total_vendido = producto.ventas.aggregate(
            total=Sum('cantidad')
        )['total'] or 0

        respuesta = ""
        if not es_exacto and similitud < 100:
            respuesta += f"💡 <em>Encontré: <strong>{producto.nombre}</strong></em><br><br>"
        
        respuesta += f"""
        <strong>📦 {producto.nombre}</strong>
        <table style="width:100%; border-collapse: collapse; margin-top:8px;">
            <tr>
                <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">💰 Precio de venta</td>
                <td style="padding:6px; border:1px solid #ddd;">${producto.precio_venta}</td>
            </tr>
            <tr>
                <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">📊 Stock actual</td>
                <td style="padding:6px; border:1px solid #ddd;">{producto.stock_actual} unidades</td>
            </tr>
            <tr>
                <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">⚠️ Stock mínimo</td>
                <td style="padding:6px; border:1px solid #ddd;">{producto.stock_minimo} unidades</td>
            </tr>
            <tr>
                <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">🔥 Total vendido</td>
                <td style="padding:6px; border:1px solid #ddd;">{total_vendido} unidades</td>
            </tr>
            <tr>
                <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">📁 Categoría</td>
                <td style="padding:6px; border:1px solid #ddd;">{producto.categoria.nombre}</td>
            </tr>
        </table>
        """
        
        if producto.necesita_reposicion:
            respuesta += "\n\n⚠️ <strong>¡Atención!</strong> Este producto necesita reposición"
        
        return respuesta

    # 🔥 PRODUCTOS MÁS VENDIDOS (AHORA CON TABLA)
    if accion == "productos_mas_vendidos":
        productos = (
            Producto.objects
            .annotate(total_vendido=Sum("ventas__cantidad"))
            .filter(total_vendido__isnull=False)
            .order_by("-total_vendido")[:5]
        )

        if not productos:
            return "📊 Aún no hay ventas registradas."

        respuesta = """
        <strong>🔥 Productos más vendidos</strong>
        <table style="width:100%; border-collapse: collapse; margin-top:8px;">
            <thead>
                <tr style="background:#ef476f; color:white;">
                    <th style="padding:8px; border:1px solid #ddd; text-align:left;">🏆</th>
                    <th style="padding:8px; border:1px solid #ddd; text-align:left;">Producto</th>
                    <th style="padding:8px; border:1px solid #ddd; text-align:center;">Vendidos</th>
                    <th style="padding:8px; border:1px solid #ddd; text-align:right;">Precio</th>
                </tr>
            </thead>
            <tbody>
        """

        # Emojis de medallas para top 3
        medallas = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
        
        for i, p in enumerate(productos):
            # Color alternado para filas
            bg_color = '#f8f9fa' if i % 2 == 0 else 'white'
            
            respuesta += f"""
            <tr style="background:{bg_color};">
                <td style="padding:8px; border:1px solid #ddd; text-align:center; font-size:20px;">
                    {medallas[i]}
                </td>
                <td style="padding:8px; border:1px solid #ddd;">
                    <strong>{p.nombre}</strong>
                </td>
                <td style="padding:8px; border:1px solid #ddd; text-align:center;">
                    <strong style="color:#06D6A0;">{p.total_vendido}</strong> unidades
                </td>
                <td style="padding:8px; border:1px solid #ddd; text-align:right;">
                    ${p.precio_venta}
                </td>
            </tr>
            """

        respuesta += "</tbody></table>"
        
        # Agregar total de unidades vendidas
        total_unidades = sum(p.total_vendido for p in productos)
        respuesta += f"<br><em>📊 Total vendido (Top 5): <strong>{total_unidades}</strong> unidades</em>"
        
        return respuesta
    
    # 📋 LISTAR PRODUCTOS
    if accion == "listar_productos":
        productos = Producto.objects.filter(activo=True)

        if not productos.exists():
            return "📦 No tienes productos registrados"

        respuesta = """
        <strong>📦 Productos registrados</strong>
        <table style="width:100%; border-collapse: collapse; margin-top:8px;">
            <thead>
                <tr style="background:#4f46e5; color:white;">
                    <th style="padding:6px; border:1px solid #ddd;">Producto</th>
                    <th style="padding:6px; border:1px solid #ddd;">Stock</th>
                    <th style="padding:6px; border:1px solid #ddd;">Precio</th>
                </tr>
            </thead>
            <tbody>
        """

        for p in productos:
            respuesta += f"""
            <tr>
                <td style="padding:6px; border:1px solid #ddd;">{p.nombre}</td>
                <td style="padding:6px; border:1px solid #ddd; text-align:center;">
                    {p.stock_actual}
                </td>
                <td style="padding:6px; border:1px solid #ddd;">
                    ${p.precio_venta}
                </td>
            </tr>
            """

        respuesta += "</tbody></table>"
        return respuesta

    # 🤔 ACLARACIÓN
    if accion == "pedir_aclaracion":
        return "🤔 ¿Podrías darme más detalles?"

    return "❌ No entendí la acción"
