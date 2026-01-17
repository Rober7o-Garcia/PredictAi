// Variables globales
let chartInstance = null;
let updateInterval = null;

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    // Iniciar actualizaciones automáticas cada 10 segundos
    updateInterval = setInterval(updateDashboard, 10000);
    
    // Mostrar indicador de actualización
    createUpdateIndicator();
});

// Crear indicador de actualización
function createUpdateIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'update-indicator';
    indicator.innerHTML = '<span class="pulse-dot"></span> Actualización automática activa';
    indicator.style.cssText = `
        position: fixed;
        top: 70px;
        right: 20px;
        background: rgba(6, 214, 160, 0.9);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    `;
    document.body.appendChild(indicator);
}

// Función para actualizar el dashboard
async function updateDashboard() {
    try {
        showUpdateAnimation();
        
        const response = await fetch('/companies/api/dashboard-data/');
        const data = await response.json();
        
        // Actualizar métricas principales
        updateMetrics(data);
        
        // Actualizar tabla de productos top
        updateTopProductos(data.productos_top);
        
        // Actualizar productos a reponer
        updateProductosReponer(data.productos_reponer, data.productos_reponer_count);
        
        // Actualizar gráfico
        updateChart(data.labels_semana, data.datos_semana);
        
        hideUpdateAnimation();
    } catch (error) {
        console.error('Error al actualizar dashboard:', error);
    }
}

// Mostrar animación de actualización
function showUpdateAnimation() {
    const indicator = document.getElementById('update-indicator');
    if (indicator) {
        indicator.style.background = 'rgba(102, 126, 234, 0.9)';
        indicator.innerHTML = '<span class="pulse-dot"></span> Actualizando...';
    }
}

function hideUpdateAnimation() {
    const indicator = document.getElementById('update-indicator');
    if (indicator) {
        setTimeout(() => {
            indicator.style.background = 'rgba(6, 214, 160, 0.9)';
            indicator.innerHTML = '<span class="pulse-dot"></span> Actualización automática activa';
        }, 500);
    }
}

// Actualizar métricas principales
function updateMetrics(data) {
    animateValue('ventas-hoy', data.ventas_hoy);
    animateValue('ventas-mes', data.ventas_mes);
    animateValue('ganancia-mes', data.ganancia_mes);
    animateValue('productos-reponer', data.productos_reponer_count);
}

// Animar cambio de valores
function animateValue(elementClass, newValue) {
    const elements = document.querySelectorAll(`.${elementClass}`);
    elements.forEach(element => {
        const currentValue = parseFloat(element.textContent.replace(/[$,]/g, '')) || 0;
        
        if (currentValue !== newValue) {
            element.style.transform = 'scale(1.1)';
            element.style.transition = 'transform 0.3s ease';
            
            setTimeout(() => {
                if (elementClass.includes('reponer')) {
                    element.textContent = newValue;
                } else {
                    element.textContent = '$' + newValue.toFixed(2);
                }
                element.style.transform = 'scale(1)';
            }, 150);
        }
    });
}

// Actualizar tabla de productos top
function updateTopProductos(productos) {
    const tbody = document.querySelector('.top-productos-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    productos.forEach(prod => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${prod.producto__nombre}</strong></td>
            <td class="text-end d-none d-sm-table-cell">
                <span class="badge-success">${prod.total}</span>
            </td>
            <td class="text-end"><strong>$${parseFloat(prod.ingresos).toFixed(2)}</strong></td>
        `;
        row.style.animation = 'fadeInUp 0.3s ease-out';
        tbody.appendChild(row);
    });
}

// Actualizar productos a reponer
function updateProductosReponer(productos, count) {
    const tbody = document.querySelector('.reponer-table tbody');
    if (!tbody) return;
    
    if (productos.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="3" class="text-center text-muted">Todo en orden ✓</td></tr>
        `;
        return;
    }
    
    tbody.innerHTML = '';
    
    productos.forEach(prod => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${prod.nombre.split(' ').slice(0, 3).join(' ')}</strong></td>
            <td class="text-end">
                <span class="badge-alert">${prod.stock_actual}</span>
            </td>
            <td class="text-end d-none d-sm-table-cell">${prod.stock_minimo}</td>
        `;
        row.style.animation = 'fadeInUp 0.3s ease-out';
        tbody.appendChild(row);
    });
}

// Actualizar gráfico
function updateChart(labels, data) {
    if (chartInstance) {
        chartInstance.data.labels = labels;
        chartInstance.data.datasets[0].data = data;
        chartInstance.update('none'); // Sin animación para actualizaciones
    }
}

// Limpiar intervalo al salir de la página
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});