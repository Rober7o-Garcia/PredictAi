/**
 * ChartManager
 * Gestiona la actualización de múltiples gráficos de Chart.js
 */

class ChartManager {
    constructor(charts) {
        // ✅ Recibir charts como parámetro
        this.charts = {
            ventasMensuales: charts.ventasMensuales,
            productos: charts.productos,
            categorias: charts.categorias,
            flujoCaja: charts.flujoCaja
        };
        
        // Log para debugging
        console.log('📊 ChartManager inicializado con:', {
            ventasMensuales: !!this.charts.ventasMensuales,
            productos: !!this.charts.productos,
            categorias: !!this.charts.categorias,
            flujoCaja: !!this.charts.flujoCaja
        });
    }

    /**
     * Actualiza el gráfico de ventas mensuales
     */
    updateVentasMensuales(labels, datos) {
        if (!this.charts.ventasMensuales) {
            console.warn('⚠️ Gráfico de ventas mensuales no disponible');
            return;
        }
        
        this.charts.ventasMensuales.data.labels = labels;
        this.charts.ventasMensuales.data.datasets[0].data = datos;
        this.charts.ventasMensuales.update('active');
    }

    /**
     * Actualiza el gráfico de productos top
     */
    updateProductos(labels, datos) {
        if (!this.charts.productos) {
            console.warn('⚠️ Gráfico de productos no disponible');
            return;
        }
        
        this.charts.productos.data.labels = labels;
        this.charts.productos.data.datasets[0].data = datos;
        this.charts.productos.update('active');
    }

    /**
     * Actualiza el gráfico de categorías
     */
    updateCategorias(labels, datos) {
        if (!this.charts.categorias) {
            console.warn('⚠️ Gráfico de categorías no disponible');
            return;
        }
        
        this.charts.categorias.data.labels = labels;
        this.charts.categorias.data.datasets[0].data = datos;
        this.charts.categorias.update('active');
    }

    /**
     * Actualiza el gráfico de flujo de caja
     */
    updateFlujoCaja(labels, ingresos, egresos) {
        if (!this.charts.flujoCaja) {
            console.warn('⚠️ Gráfico de flujo de caja no disponible');
            return;
        }
        
        this.charts.flujoCaja.data.labels = labels;
        this.charts.flujoCaja.data.datasets[0].data = ingresos;
        this.charts.flujoCaja.data.datasets[1].data = egresos;
        this.charts.flujoCaja.update('active');
    }

    /**
     * Actualiza todos los gráficos con nuevos datos
     */
    updateAll(data) {
        if (data.labels_meses && data.datos_meses) {
            this.updateVentasMensuales(data.labels_meses, data.datos_meses);
        }
        
        if (data.labels_productos && data.datos_productos) {
            this.updateProductos(data.labels_productos, data.datos_productos);
        }
        
        if (data.labels_categorias && data.datos_categorias) {
            this.updateCategorias(data.labels_categorias, data.datos_categorias);
        }
        
        if (data.labels_flujo && data.datos_ingresos && data.datos_egresos) {
            this.updateFlujoCaja(data.labels_flujo, data.datos_ingresos, data.datos_egresos);
        }
    }
}

export default ChartManager;