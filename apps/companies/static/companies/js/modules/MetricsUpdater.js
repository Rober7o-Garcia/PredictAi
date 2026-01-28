/**
 * MetricsUpdater
 * Actualiza las métricas KPI en el DOM
 */

class MetricsUpdater {
    /**
     * Actualiza un elemento del DOM con nuevo valor
     */
    updateElement(selector, value, prefix = '$', suffix = '') {
        const element = document.querySelector(selector);
        if (!element) return;
        
        // Animación de cambio
        element.style.transition = 'all 0.3s ease';
        element.style.transform = 'scale(1.1)';
        
        setTimeout(() => {
            element.textContent = `${prefix}${value}${suffix}`;
            element.style.transform = 'scale(1)';
        }, 150);
    }

    /**
     * Actualiza todas las métricas KPI
     */
    updateMetrics(data) {
        if (data.liquidez !== undefined) {
            this.updateElement('.liquidez-mes', parseFloat(data.liquidez).toFixed(2));
        }
        
        if (data.margen_neto_porcentaje !== undefined) {
            this.updateElement('.margen-neto', parseFloat(data.margen_neto_porcentaje).toFixed(1), '', '%');
        }
        
        if (data.ticket_promedio !== undefined) {
            this.updateElement('.ticket-promedio', parseFloat(data.ticket_promedio).toFixed(2));
        }
        
        if (data.ventas_mes !== undefined) {
            this.updateElement('.ventas-mes', parseFloat(data.ventas_mes).toFixed(2));
        }
        
        if (data.productos_reponer_count !== undefined) {
            this.updateElement('.productos-reponer', data.productos_reponer_count, '', '');
        }
    }

    /**
     * Muestra indicador visual de actualización
     */
    showUpdateIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.innerHTML = '🔄 Actualizando...';
        indicator.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #43e97b;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            z-index: 9999;
            animation: slideInRight 0.3s ease;
        `;
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => indicator.remove(), 300);
        }, 2000);
    }
}

export default MetricsUpdater;