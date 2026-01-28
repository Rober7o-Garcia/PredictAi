/**
 * DashboardAPI
 * Maneja todas las comunicaciones con el backend
 */

class DashboardAPI {
    /**
     * @param {string} apiUrl - URL del endpoint de la API
     */
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    /**
     * Obtiene los datos del dashboard desde el backend
     * @returns {Promise<Object>} Datos del dashboard
     */
    async fetchDashboardData() {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    /**
     * Manejo centralizado de errores
     * @param {Error} error - Error capturado
     */
    handleError(error) {
        console.error('Error en DashboardAPI:', error);
        
        // Aquí puedes agregar lógica adicional:
        // - Enviar error a servicio de logging
        // - Mostrar notificación al usuario
        // - Reintentar la petición
    }
}

export default DashboardAPI;