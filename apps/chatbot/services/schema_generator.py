def get_database_schema():
        """
        Genera descripción completa del esquema de la BD para el LLM
        """
        return """
    # ESQUEMA DE BASE DE DATOS - SISTEMA DE NEGOCIO (MIPYME)

    CONTEXTO: Este sistema funciona para CUALQUIER tipo de negocio (tiendas, restaurantes, 
    farmacias, librerías, ferreterías, etc.). Los datos se adaptan al tipo de negocio del usuario.

    ## Tablas Principales:

    ### companies_producto
    Columns:
    - id: INTEGER PRIMARY KEY
    - nombre: VARCHAR(200) - Nombre del producto/servicio (puede ser cualquier cosa que venda el negocio)
    - precio_venta: DECIMAL(10,2) - Precio al cliente
    - precio_compra: DECIMAL(10,2) - Costo de adquisición
    - stock_actual: INTEGER - Unidades disponibles
    - stock_minimo: INTEGER - Nivel mínimo de reposición
    - activo: BOOLEAN - Si está disponible para venta
    - categoria_id: INTEGER - FK a companies_categoria

    ### companies_venta
    Columns:
    - id: INTEGER PRIMARY KEY
    - fecha: DATETIME - Fecha y hora exacta de la venta
    - total: DECIMAL(10,2) - Monto total de la transacción
    - subtotal: DECIMAL(10,2)
    - descuento: DECIMAL(10,2)

    ### companies_itemventa
    Columns:
    - id: INTEGER PRIMARY KEY
    - venta_id: INTEGER - FK a companies_venta
    - producto_id: INTEGER - FK a companies_producto
    - cantidad: INTEGER - Unidades vendidas
    - precio_unitario: DECIMAL(10,2) - Precio al que se vendió
    - costo_unitario: DECIMAL(10,2) - Costo del producto en esa venta

    ### companies_categoria
    Columns:
    - id: INTEGER PRIMARY KEY
    - nombre: VARCHAR(100) - Nombre de la categoría

    ## Relaciones:
    - Producto → Categoria (Many-to-One)
    - ItemVenta → Venta (Many-to-One)
    - ItemVenta → Producto (Many-to-One)

    ## Cálculos Importantes:
    - Ganancia por item: (precio_unitario - costo_unitario) * cantidad
    - Margen: ((precio_unitario - costo_unitario) / precio_unitario) * 100
    - Stock crítico: WHERE stock_actual <= stock_minimo

    ## Funciones de Fecha SQLite:
    - Hoy: DATE('now')
    - Ayer: DATE('now', '-1 day')
    - Última semana: DATE('now', '-7 days')
    - Último mes: DATE('now', '-1 month')
    - Año pasado: DATE('now', '-1 year')
    - Extraer día de semana: strftime('%w', fecha) -- 0=Domingo, 6=Sábado
    - Extraer mes: strftime('%m', fecha)
    - Extraer año: strftime('%Y', fecha)

    ## IMPORTANTE - Búsqueda de Productos:
    Cuando busques un producto específico por nombre, usa LIKE con comodines para ser flexible:
    - WHERE nombre LIKE '%término%' (busca en cualquier parte del nombre)
    - WHERE LOWER(nombre) LIKE LOWER('%término%') (case-insensitive)
    """


def get_sample_queries():
        """
        Ejemplos de queries comunes para ayudar al LLM
        """
        return """
    ## EJEMPLOS DE QUERIES ÚTILES:

    ### Ventas del día actual:
    SELECT SUM(total) as total_dia, COUNT(*) as num_ventas
    FROM companies_venta 
    WHERE DATE(fecha) = DATE('now');

    ### Productos más vendidos:
    SELECT 
        p.nombre, 
        SUM(iv.cantidad) as total_vendido,
        SUM(iv.cantidad * iv.precio_unitario) as ingresos
    FROM companies_producto p
    JOIN companies_itemventa iv ON p.id = iv.producto_id
    GROUP BY p.id, p.nombre
    ORDER BY total_vendido DESC
    LIMIT 5;

    ### Productos bajo stock:
    SELECT nombre, stock_actual, stock_minimo
    FROM companies_producto
    WHERE stock_actual <= stock_minimo AND activo = 1;

    ### Margen de ganancia total:
    SELECT 
        SUM(iv.cantidad * iv.precio_unitario) as ingresos,
        SUM(iv.cantidad * iv.costo_unitario) as costos,
        SUM(iv.cantidad * (iv.precio_unitario - iv.costo_unitario)) as ganancia
    FROM companies_itemventa iv;

    ### Ventas por categoría:
    SELECT 
        c.nombre as categoria,
        COUNT(DISTINCT v.id) as num_ventas, 
        SUM(v.total) as total_ingresos
    FROM companies_categoria c
    JOIN companies_producto p ON c.id = p.categoria_id
    JOIN companies_itemventa iv ON p.id = iv.producto_id
    JOIN companies_venta v ON iv.venta_id = v.id
    GROUP BY c.id, c.nombre
    ORDER BY total_ingresos DESC;

    ### Ventas del año pasado (para recomendaciones):
    SELECT 
        p.nombre,
        SUM(iv.cantidad) as total_vendido,
        COUNT(DISTINCT v.id) as num_transacciones,
        SUM(iv.cantidad * iv.precio_unitario) as ingresos
    FROM companies_itemventa iv
    JOIN companies_producto p ON iv.producto_id = p.id
    JOIN companies_venta v ON iv.venta_id = v.id
    WHERE strftime('%Y', v.fecha) = strftime('%Y', DATE('now', '-1 year'))
    GROUP BY p.id, p.nombre
    ORDER BY total_vendido DESC;

    ### Tendencia de ventas por mes:
    SELECT 
        strftime('%Y-%m', fecha) as mes,
        COUNT(*) as num_ventas,
        SUM(total) as ingresos
    FROM companies_venta
    GROUP BY mes
    ORDER BY mes DESC;

    ### Productos con mejor crecimiento:
    SELECT 
        p.nombre,
        SUM(CASE WHEN v.fecha >= DATE('now', '-30 days') THEN iv.cantidad ELSE 0 END) as ultimo_mes,
        SUM(CASE WHEN v.fecha >= DATE('now', '-60 days') AND v.fecha < DATE('now', '-30 days') THEN iv.cantidad ELSE 0 END) as mes_anterior
    FROM companies_producto p
    LEFT JOIN companies_itemventa iv ON p.id = iv.producto_id
    LEFT JOIN companies_venta v ON iv.venta_id = v.id
    GROUP BY p.id, p.nombre
    HAVING ultimo_mes > 0 OR mes_anterior > 0;

    ### Ventas por día de la semana:
    SELECT 
        CASE strftime('%w', fecha)
            WHEN '0' THEN 'Domingo'
            WHEN '1' THEN 'Lunes'
            WHEN '2' THEN 'Martes'
            WHEN '3' THEN 'Miércoles'
            WHEN '4' THEN 'Jueves'
            WHEN '5' THEN 'Viernes'
            WHEN '6' THEN 'Sábado'
        END as dia,
        COUNT(*) as num_ventas,
        SUM(total) as ingresos
    FROM companies_venta
    GROUP BY strftime('%w', fecha)
    ORDER BY num_ventas DESC;
    """