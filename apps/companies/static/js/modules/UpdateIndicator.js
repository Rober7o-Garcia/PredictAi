/**
 * UpdateIndicator
 * Gestiona el indicador visual de actualización
 */

class UpdateIndicator {
    /**
     * @param {Object} config - Configuración del indicador
     */
    constructor(config = {}) {
        this.config = {
            position: {
                top: '70px',
                right: '20px',
                ...config.position
            },
            text: {
                active: 'Actualización automática activa',
                updating: 'Actualizando...',
                ...config.text
            },
            colors: {
                active: 'rgba(6, 214, 160, 0.9)',
                updating: 'rgba(102, 126, 234, 0.9)',
                ...config.colors
            }
        };

        this.element = null;
    }

    /**
     * Crea el indicador en el DOM
     */
    create() {
        // Si ya existe, no crear otro
        if (this.element) {
            console.warn('Indicador ya existe');
            return;
        }

        // Crear elemento
        this.element = document.createElement('div');
        this.element.id = 'update-indicator';
        
        // Aplicar estilos
        this.element.style.cssText = `
            position: fixed;
            top: ${this.config.position.top};
            right: ${this.config.position.right};
            background: ${this.config.colors.active};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.3s ease;
        `;

        // Contenido inicial
        this.element.innerHTML = `
            <span class="pulse-dot"></span> 
            ${this.config.text.active}
        `;

        // Agregar CSS para el pulse-dot
        this.addPulseDotStyles();

        // Agregar al body
        document.body.appendChild(this.element);
    }

    /**
     * Agrega los estilos del pulse-dot si no existen
     */
    addPulseDotStyles() {
        // Verificar si ya existe el estilo
        if (document.getElementById('pulse-dot-styles')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'pulse-dot-styles';
        style.textContent = `
            .pulse-dot {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: white;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% {
                    opacity: 1;
                    transform: scale(1);
                }
                50% {
                    opacity: 0.5;
                    transform: scale(0.8);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Cambia el indicador a estado "actualizando"
     */
    showUpdating() {
        if (!this.element) return;

        this.element.style.background = this.config.colors.updating;
        this.element.innerHTML = `
            <span class="pulse-dot"></span> 
            ${this.config.text.updating}
        `;
    }

    /**
     * Cambia el indicador a estado "activo"
     */
    showActive() {
        if (!this.element) return;

        this.element.style.background = this.config.colors.active;
        this.element.innerHTML = `
            <span class="pulse-dot"></span> 
            ${this.config.text.active}
        `;
    }

    /**
     * Elimina el indicador del DOM
     */
    remove() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
            this.element = null;
        }
    }
}

export default UpdateIndicator;