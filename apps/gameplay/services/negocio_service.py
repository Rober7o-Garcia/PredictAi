from apps.companies.models import Producto

def ejecutar_accion(data):
    accion = data.get("accion")

    if accion == "registrar_venta":
        producto = Producto.objects.filter(
            nombre__icontains=data.get("producto", "")
        ).first()

        if not producto:
            return "❌ No encontré ese producto"

        cantidad = data.get("cantidad", 0)

        if producto.stock_actual < cantidad:
            return (
                f"⚠️ Stock insuficiente.\n"
                f"Disponible: {producto.stock_actual}"
            )

        producto.stock_actual -= cantidad
        producto.save()

        return (
            f"✅ Venta registrada.\n"
            f"📦 Stock actual de {producto.nombre}: {producto.stock_actual}"
        )

    if accion == "consultar_stock":
        producto = Producto.objects.filter(
            nombre__icontains=data.get("producto", "")
        ).first()

        if not producto:
            return "❌ Producto no encontrado"

        return f"📦 {producto.nombre}: {producto.stock_actual} unidades"

    if accion == "pedir_aclaracion":
        return "🤔 ¿Podrías darme más detalles?"

    return "❌ No entendí la acción"
