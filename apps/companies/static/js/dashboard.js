/**
 * Dashboard - Entry Point con Firebase
 * Orquesta todos los módulos del dashboard con sincronización en tiempo real
 */

import DashboardAPI from './modules/DashboardAPI.js';
import DashboardUI from './modules/DashboardUI.js';
import MetricsUpdater from './modules/MetricsUpdater.js';
import ChartManager from './modules/ChartManager.js';
import UpdateIndicator from './modules/UpdateIndicator.js';
import FirebaseSync from './modules/FirebaseSync.js';
import ChartsInit from './modules/ChartsInit.js';


class Dashboard {
    constructor() {
        // Módulos de API y UI
        this.api = new DashboardAPI('/companies/api/dashboard-data/');
        this.ui = new DashboardUI();
        this.metrics = new MetricsUpdater(300);
        this.indicator = new UpdateIndicator();
        
        // Charts (se inicializarán después de obtener datos)
        this.chartsInit = null;
        this.chartManager = null;
        
        // Firebase Sync para tiempo real
        this.firebaseSync = new FirebaseSync(
            'demo_company',
            () => this.onFirebaseUpdate()
        );
    }

    /**
     * Inicializa el dashboard
     */
    async initialize() {
        try {
            console.log('🚀 Inicializando Dashboard con Firebase...');

            // Crear indicador de actualización
            this.indicator.create();

            // Primera carga: obtener datos y crear gráficos
            await this.firstLoad();

            // Iniciar listener de Firebase
            this.firebaseSync.startListening();

            // Configurar cleanup
            this.setupCleanup();

            console.log('✅ Dashboard inicializado con sincronización en tiempo real');
        } catch (error) {
            console.error('❌ Error al inicializar dashboard:', error);
        }
    }

    /**
     * Primera carga: inicializa gráficos con datos del backend
     */
    async firstLoad() {
        try {
            this.indicator.showUpdating();

            // Obtener datos iniciales
            const data = await this.api.fetchDashboardData();

            // Inicializar gráficos con los datos
            this.chartsInit = new ChartsInit(data);

            // Crear ChartManager con los gráficos inicializados
            this.chartManager = new ChartManager(this.chartsInit.getCharts());

            // Actualizar métricas y tablas
            this.metrics.updateMetrics(data);
            this.ui.updateAllTables(data);

            this.indicator.showActive();
        } catch (error) {
            console.error('Error en primera carga:', error);
            this.indicator.showActive();
        }
    }

    /**
     * Callback cuando Firebase detecta cambios
     */
    onFirebaseUpdate() {
        console.log('🔔 Firebase notificó cambio, actualizando dashboard...');
        this.update();
    }

    /**
     * Actualiza todos los datos del dashboard (después de cambios)
     */
    async update() {
        try {
            this.indicator.showUpdating();

            // Obtener nuevos datos
            const data = await this.api.fetchDashboardData();

            // Actualizar métricas KPI
            this.metrics.updateMetrics(data);

            // Actualizar tablas
            this.ui.updateAllTables(data);

            // Actualizar todos los gráficos
            if (this.chartManager) {
                this.chartManager.updateAll(data);
            }

            this.indicator.showActive();
        } catch (error) {
            console.error('Error al actualizar dashboard:', error);
            this.indicator.showActive();
        }
    }

    /**
     * Configura el cleanup cuando el usuario sale de la página
     */
    setupCleanup() {
        // Cleanup al cerrar
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        // Pausar/reanudar según visibilidad
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('⏸️ Usuario cambió de pestaña, pausando listener');
                this.firebaseSync.stopListening();
            } else {
                console.log('▶️ Usuario volvió, reanudando listener');
                this.firebaseSync.startListening();
                this.update(); // Actualizar inmediatamente al volver
            }
        });
    }

    /**
     * Limpia recursos antes de salir
     */
    cleanup() {
        console.log('🧹 Limpiando recursos del dashboard...');
        this.firebaseSync.stopListening();
        this.indicator.remove();
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.initialize();
});