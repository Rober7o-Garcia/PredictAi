/**
 * DashboardUI
 * Maneja todas las actualizaciones del DOM/UI
 */

class DashboardUI {
    /**
     * Actualiza la tabla de productos más vendidos
     * @param {Array} productos - Array de productos top
     */
    updateTopProductos(productos) {
        const tbody = document.querySelector('.top-productos-table tbody');
        if (!tbody) {
            console.warn('Tabla de top productos no encontrada');
            return;
        }

        // Limpiar contenido existente
        tbody.innerHTML = '';

        // Si no hay productos, mostrar mensaje
        if (!productos || productos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-muted">
                        No hay datos de ventas aún
                    </td>
                </tr>
            `;
            return;
        }

        // Crear filas para cada producto
        productos.forEach(prod => {
            const row = this.createTopProductoRow(prod);
            tbody.appendChild(row);
        });
    }

    /**
     * Crea una fila para la tabla de top productos
     * @param {Object} producto - Datos del producto
     * @returns {HTMLElement} Elemento TR
     */
    createTopProductoRow(producto) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${producto.producto__nombre}</strong></td>
            <td class="text-end d-none d-sm-table-cell">
                <span class="badge-success">${producto.total}</span>
            </td>
            <td class="text-end">
                <strong>$${parseFloat(producto.ingresos).toFixed(2)}</strong>
            </td>
        `;
        row.style.animation = 'fadeInUp 0.3s ease-out';
        return row;
    }

    /**
     * Actualiza la tabla de productos a reponer
     * @param {Array} productos - Array de productos con stock bajo
     */
    updateProductosReponer(productos) {
        const tbody = document.querySelector('.reponer-table tbody');
        if (!tbody) {
            console.warn('Tabla de productos a reponer no encontrada');
            return;
        }

        // Limpiar contenido existente
        tbody.innerHTML = '';

        // Si no hay productos, mostrar mensaje positivo
        if (!productos || productos.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-success">
                        ✓ Todo el inventario está en orden
                    </td>
                </tr>
            `;
            return;
        }

        // Crear filas para cada producto
        productos.forEach(prod => {
            const row = this.createProductoReponerRow(prod);
            tbody.appendChild(row);
        });
    }

    /**
     * Crea una fila para la tabla de productos a reponer
     * @param {Object} producto - Datos del producto
     * @returns {HTMLElement} Elemento TR
     */
    createProductoReponerRow(producto) {
        const row = document.createElement('tr');
        
        // Truncar nombre si es muy largo
        const nombreTruncado = producto.nombre.length > 30 
            ? producto.nombre.substring(0, 30) + '...'
            : producto.nombre;

        row.innerHTML = `
            <td><strong>${nombreTruncado}</strong></td>
            <td>${producto.categoria || 'Sin categoría'}</td>
            <td class="text-end">
                <span class="badge-alert">${producto.stock_actual}</span>
            </td>
            <td class="text-end">${producto.stock_minimo}</td>
            <td class="text-end">${producto.proveedor || 'Sin proveedor'}</td>
        `;
        row.style.animation = 'fadeInUp 0.3s ease-out';
        return row;
    }

    /**
     * Actualiza todas las tablas del dashboard
     * @param {Object} data - Datos completos del dashboard
     */
    updateAllTables(data) {
        this.updateProductosReponer(data.productos_reponer);
    }
}

export default DashboardUI;