/**
 * ChartsInit
 * Inicializa todos los gráficos del dashboard con Chart.js
 * Mantiene la configuración centralizada y reutilizable
 */

class ChartsInit {
    constructor(data) {
        this.data = data;
        this.charts = {};
        this.initializeAll();
    }

    /**
     * Configuración global de Chart.js
     */
    setGlobalConfig() {
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.color = '#4a5568';
    }

    /**
     * Inicializa todos los gráficos
     */
    initializeAll() {
        this.setGlobalConfig();
        this.initVentasMensuales();
        this.initProductos();
        this.initCategorias();
        this.initFlujoCaja();
    }

    /**
     * 1. Gráfico: Ventas Mensuales (Líneas)
     */
    initVentasMensuales() {
        const ctx = document.getElementById('ventasMensualesChart');
        if (!ctx) return;

        this.charts.ventasMensuales = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.data.labels_meses || [],
                datasets: [{
                    label: 'Ventas ($)',
                    data: this.data.datos_meses || [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: (context) => `Ventas: $${context.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * 2. Gráfico: Productos Top (Barras Horizontales)
     */
    initProductos() {
        const ctx = document.getElementById('productosChart');
        if (!ctx) return;

        this.charts.productos = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.data.labels_productos || [],
                datasets: [{
                    label: 'Ingresos ($)',
                    data: this.data.datos_productos || [],
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#4facfe',
                        '#43e97b', '#fa709a', '#fee140', '#30cfd0',
                        '#a8edea', '#fbc2eb'
                    ],
                    borderRadius: 8,
                    borderWidth: 0
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {
                            label: (context) => `Ingresos: $${context.parsed.x.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    y: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * 3. Gráfico: Ventas por Categoría (Donut)
     */
    initCategorias() {
        const ctx = document.getElementById('categoriasChart');
        if (!ctx) return;

        this.charts.categorias = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: this.data.labels_categorias || [],
                datasets: [{
                    data: this.data.datos_categorias || [],
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#4facfe',
                        '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                    ],
                    borderWidth: 0,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * 4. Gráfico: Flujo de Caja (Área)
     */
    initFlujoCaja() {
        const ctx = document.getElementById('flujoCajaChart');
        if (!ctx) return;

        this.charts.flujoCaja = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.data.labels_flujo || [],
                datasets: [
                    {
                        label: 'Ingresos',
                        data: this.data.datos_ingresos || [],
                        borderColor: '#43e97b',
                        backgroundColor: 'rgba(67, 233, 123, 0.2)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#43e97b',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        borderWidth: 3
                    },
                    {
                        label: 'Egresos',
                        data: this.data.datos_egresos || [],
                        borderColor: '#fa709a',
                        backgroundColor: 'rgba(250, 112, 154, 0.2)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#fa709a',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {
                            label: (context) => `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: 'rgba(0,0,0,0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * Obtiene todos los gráficos inicializados
     */
    getCharts() {
        return this.charts;
    }
}

export default ChartsInit;