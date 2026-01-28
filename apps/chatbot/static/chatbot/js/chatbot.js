// ==========================================
// CONFIGURACIÓN Y CONSTANTES
// ==========================================
const CONFIG = {
    TYPING_SPEED: 50,
    TITLE_FADE_DURATION: 200,
    MESSAGE_ANIMATION_DURATION: 300
};


// ==========================================
// MÓDULO: Modal de confirmación
// ==========================================
const Modal = {
    element: null,
    resolveCallback: null,

    init() {
        this.element = document.getElementById('confirmModal');
        
        document.getElementById('modalCancel').addEventListener('click', () => {
            this.hide(false);
        });

        document.getElementById('modalConfirm').addEventListener('click', () => {
            this.hide(true);
        });

        // Cerrar al hacer click fuera del modal
        this.element.addEventListener('click', (e) => {
            if (e.target === this.element) {
                this.hide(false);
            }
        });
    },

    show(title, message, confirmText = 'Confirmar', isDanger = false) {
        return new Promise((resolve) => {
            this.resolveCallback = resolve;

            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalMessage').textContent = message;
            document.getElementById('modalConfirm').textContent = confirmText;

            const confirmBtn = document.getElementById('modalConfirm');
            if (isDanger) {
                confirmBtn.classList.add('danger');
            } else {
                confirmBtn.classList.remove('danger');
            }

            this.element.classList.add('active');
        });
    },

    hide(result) {
        this.element.classList.remove('active');
        if (this.resolveCallback) {
            this.resolveCallback(result);
            this.resolveCallback = null;
        }
    }
};

// ==========================================
// MÓDULO: Notificaciones (Toast)
// ==========================================
const Notification = {
    container: null,
    queue: [],

    init() {
        this.container = document.getElementById('notificationContainer');
    },

    show(type, title, message, duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        notification.innerHTML = `
            <div class="notification-icon">${icons[type] || 'ℹ'}</div>
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">×</button>
        `;

        this.container.appendChild(notification);

        // Animación de entrada
        setTimeout(() => notification.classList.add('show'), 10);

        // Event listener para cerrar
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hide(notification);
        });

        // Auto-cerrar después de duration
        if (duration > 0) {
            setTimeout(() => this.hide(notification), duration);
        }

        return notification;
    },

    hide(notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    },

    success(title, message, duration) {
        return this.show('success', title, message, duration);
    },

    error(title, message, duration) {
        return this.show('error', title, message, duration);
    },

    warning(title, message, duration) {
        return this.show('warning', title, message, duration);
    },

    info(title, message, duration) {
        return this.show('info', title, message, duration);
    }
};

const MESSAGES = {
    NO_CSRF_TOKEN: {
        title: 'Error de seguridad',
        message: 'Token CSRF no disponible'
    },
    SERVER_ERROR: {
        title: 'Error de conexión',
        message: 'No se pudo comunicar con el servidor'
    },
    INVALID_RESPONSE: {
        title: 'Error',
        message: 'Respuesta inválida del servidor'
    },
    EMPTY_CONVERSATION: {
        title: 'Conversación vacía',
        message: 'Escribe al menos un mensaje antes de crear una nueva conversación'
    },
    DELETE_CONFIRM: {
        title: 'Eliminar conversación',
        message: '¿Estás seguro de que deseas eliminar esta conversación? Esta acción no se puede deshacer.',
        confirmText: 'Eliminar'
    },
    DELETE_SUCCESS: {
        title: 'Conversación eliminada',
        message: 'La conversación se eliminó correctamente'
    },
    DELETE_ERROR: {
        title: 'Error al eliminar',
        message: 'No se pudo eliminar la conversación'
    },
    CREATE_ERROR: {
        title: 'Error al crear',
        message: 'No se pudo crear la conversación'
    }
};

// ==========================================
// ELEMENTOS DEL DOM
// ==========================================
const DOM = {
    input: document.getElementById('chatbotInput'),
    sendBtn: document.getElementById('chatbotSend'),
    messagesContainer: document.getElementById('chatbotMessages'),
    micBtn: document.getElementById('chatbotMic'),
    sidebar: document.getElementById('chatSidebar'),
    menuIcon: document.getElementById('menuIcon'),
    closeIcon: document.getElementById('closeIcon')
};

// ==========================================
// MÓDULO: API - Comunicación con el servidor
// ==========================================
const ChatAPI = {
    async sendMessage(message, conversacionId) {
        const response = await fetch('/chatbot/chat/api/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCookie('csrftoken')
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                mensaje: message,
                conversacion_id: conversacionId
            })
        });
        return response.json();
    },

    async getConversationMessages(conversacionId) {
        const response = await fetch(`/chatbot/chat/mensajes/${conversacionId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        return response.json();
    },

    async createConversation() {
        const response = await fetch('/chatbot/chat/nueva/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': Utils.getCookie('csrftoken')
            }
        });
        return response.json();
    },

    async deleteConversation(conversacionId) {
        const csrfToken = Utils.getCookie('csrftoken') || 
                         document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        if (!csrfToken) {
            throw new Error(MESSAGES.NO_CSRF_TOKEN);
        }

        const response = await fetch(`/chatbot/chat/eliminar/${conversacionId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

    async deleteConversationSilently(conversacionId) {
        try {
            const csrfToken = Utils.getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) return;

            await fetch(`/chatbot/chat/eliminar/${conversacionId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });
        } catch (error) {
            console.error('Error al eliminar conversación vacía:', error);
        }
    }

};

// ==========================================
// MÓDULO: Gestión de conversaciones vacías
// ==========================================
const EmptyConversationManager = {
    currentConversationId: null,
    conversationsWithMessages: new Set(), // ✅ Tracking de conversaciones con mensajes

    init(conversacionId) {
        this.currentConversationId = conversacionId;
        this.checkInitialMessages(); // Verificar si tiene mensajes al cargar
        this.setupBeforeUnloadHandler();
    },

    // ✅ Verificar mensajes iniciales de la conversación
    checkInitialMessages() {
        const messages = document.querySelectorAll('#chatbotMessages .message');
        if (messages.length > 0) {
            this.conversationsWithMessages.add(this.currentConversationId);
        }
    },

    // ✅ Marcar que la conversación actual tiene mensajes
    markCurrentAsHavingMessages() {
        if (this.currentConversationId) {
            this.conversationsWithMessages.add(this.currentConversationId);
            console.log(`✓ Conversación ${this.currentConversationId} marcada como con mensajes`);
        }
    },

    // ✅ Verificación instantánea usando tracking
    checkCurrentBeforeSwitchSync(newConversacionId) {
        // Si no hay conversación actual, actualizar y salir
        if (!this.currentConversationId) {
            this.currentConversationId = newConversacionId;
            return;
        }

        // Si es la misma conversación, no hacer nada
        if (this.currentConversationId === newConversacionId) {
            return;
        }

        // ✅ Verificar si la conversación actual está en el Set (tiene mensajes)
        const currentHasMessages = this.conversationsWithMessages.has(this.currentConversationId);

        // Si NO tiene mensajes, eliminar INMEDIATAMENTE
        if (!currentHasMessages) {
            this.deleteEmptyConversationSync(this.currentConversationId);
        }

        // Actualizar a la nueva conversación
        this.currentConversationId = newConversacionId;
    },

    // ✅ Eliminación síncrona e instantánea
    deleteEmptyConversationSync(conversacionId) {
        // 1. Eliminar del tracking
        this.conversationsWithMessages.delete(conversacionId);

        // 2. Eliminar del sidebar INMEDIATAMENTE
        const item = document.querySelector(`.conversacion-item[data-conversacion-id="${conversacionId}"]`);
        if (item) {
            item.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
            item.style.opacity = '0';
            item.style.transform = 'translateX(-10px)';
            
            setTimeout(() => {
                item.remove();
            }, 150);
        }

        // 3. Eliminar del backend (asíncrono en background)
        this.deleteFromBackend(conversacionId);

        console.log(`✓ Conversación vacía ${conversacionId} eliminada automáticamente`);
    },

    // Eliminar del backend en background
    async deleteFromBackend(conversacionId) {
        try {
            await ChatAPI.deleteConversationSilently(conversacionId);
        } catch (error) {
            console.error('Error al eliminar del backend:', error);
        }
    },

    // Para cuando se cierra la ventana
    async checkCurrentBeforeLeaving() {
        if (!this.currentConversationId) return;

        const currentHasMessages = this.conversationsWithMessages.has(this.currentConversationId);
        
        if (!currentHasMessages) {
            await ChatAPI.deleteConversationSilently(this.currentConversationId);
        }
    },

    setupBeforeUnloadHandler() {
        window.addEventListener('beforeunload', async (e) => {
            await this.checkCurrentBeforeLeaving();
        });

        window.addEventListener('pagehide', async () => {
            await this.checkCurrentBeforeLeaving();
        });
    }
};

// ==========================================
// MÓDULO: Navegación SPA
// ==========================================
const NavigationManager = {
    async loadConversation(conversacionId) {
        try {
            console.log('📂 Cargando conversación:', conversacionId); // ✅ LOG
            
            // Verificación SÍNCRONA e INSTANTÁNEA
            EmptyConversationManager.checkCurrentBeforeSwitchSync(conversacionId);

            // Obtener mensajes de la nueva conversación
            const data = await ChatAPI.getConversationMessages(conversacionId);
            
            console.log('📨 Mensajes recibidos:', data.mensajes.length); // ✅ LOG
            
            // Actualizar ID global
            window.CONVERSACION_ID = data.conversacion_id;
            
            // Limpiar mensajes actuales
            DOM.messagesContainer.innerHTML = '';
            
            // Actualizar título principal
            const titleElement = document.querySelector('.chatbot-title');
            titleElement.textContent = data.titulo;
            
            // Renderizar mensajes
            if (data.mensajes.length === 0) {
                this.showWelcomeMessage();
            } else {
                data.mensajes.forEach(msg => {
                    ChatUI.addMessageFromData(msg);
                });
                
                // ✅ MARCAR que esta conversación tiene mensajes
                EmptyConversationManager.conversationsWithMessages.add(data.conversacion_id);
                console.log('✅ Conversación marcada con mensajes:', data.conversacion_id); // ✅ LOG
            }
            
            console.log('📊 Estado del tracking:', EmptyConversationManager.conversationsWithMessages); // ✅ LOG
            
            // Actualizar sidebar (marcar conversación activa)
            this.updateSidebarActive(conversacionId);
            
            // Actualizar URL sin recargar
            history.pushState(
                { conversacionId: conversacionId }, 
                '', 
                `/chatbot/chat/${conversacionId}/`
            );
            
        } catch (error) {
            console.error('❌ Error al cargar conversación:', error);
            Notification.error(
                'Error al cargar',
                'No se pudo cargar la conversación'
            );
        }
    },

    addToSidebar(conversacionData) {
        const conversacionesList = document.querySelector('.conversaciones-list');
        
        // Si hay un mensaje de "No hay conversaciones", eliminarlo
        const emptyMessage = conversacionesList.querySelector('.text-muted');
        if (emptyMessage) {
            emptyMessage.remove();
        }

        // Crear el nuevo item
        const newItem = document.createElement('a');
        newItem.href = '#';
        newItem.setAttribute('data-conversacion-id', conversacionData.conversacion_id);
        newItem.className = 'conversacion-item active'; // Activa porque es la nueva
        newItem.onclick = (e) => {
            e.preventDefault();
            NavigationManager.loadConversation(conversacionData.conversacion_id);
            return false;
        };

        newItem.innerHTML = `
            <div class="conv-titulo">${conversacionData.titulo}</div>
            <div class="conv-fecha">${conversacionData.fecha_actualizacion}</div>
            <button class="btn-delete" onclick="eliminarConversacion(event, ${conversacionData.conversacion_id})">🗑️</button>
        `;

        // Animación de entrada
        newItem.style.opacity = '0';
        newItem.style.transform = 'translateX(-20px)';

        // Insertar al inicio de la lista
        conversacionesList.insertBefore(newItem, conversacionesList.firstChild);

        // Animar entrada
        setTimeout(() => {
            newItem.style.transition = 'all 0.3s ease';
            newItem.style.opacity = '1';
            newItem.style.transform = 'translateX(0)';
        }, 10);

        // Desactivar otras conversaciones
        document.querySelectorAll('.conversacion-item').forEach(item => {
            if (item !== newItem) {
                item.classList.remove('active');
            }
        });
    },


    removeFromSidebar(conversacionId) {
        const item = document.querySelector(`.conversacion-item[data-conversacion-id="${conversacionId}"]`);
        if (item) {
            // Animación de salida
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                item.remove();
                
                // Si no quedan conversaciones, mostrar mensaje
                const remainingConversations = document.querySelectorAll('.conversacion-item');
                if (remainingConversations.length === 0) {
                    const conversacionesList = document.querySelector('.conversaciones-list');
                    conversacionesList.innerHTML = '<p class="text-muted text-center mt-3">No hay conversaciones</p>';
                }
            }, 300); // Duración de la animación
        }
    },

    showWelcomeMessage() {
        DOM.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h3>¡Hola! Soy tu asistente</h3>
                <p>¿En qué puedo ayudarte hoy?</p>
                <div class="welcome-suggestions">
                    <div class="suggestion-chip" data-message="¿Cuáles son los productos más vendidos?">
                        ¿Cuáles son los productos más vendidos?
                    </div>
                    <div class="suggestion-chip" data-message="Registrar venta">
                        Registrar una venta
                    </div>
                    <div class="suggestion-chip" data-message="¿Qué productos necesito reponer?">
                        ¿Qué productos necesito reponer?
                    </div>
                </div>
            </div>
        `;
        
        // Re-attachar event listeners a los nuevos chips
        this.attachSuggestionListeners();
    },

    attachSuggestionListeners() {
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const message = chip.getAttribute('data-message');
                DOM.input.value = message;
                MessageHandler.send();
            });
        });
    },

    updateSidebarActive(conversacionId) {
        document.querySelectorAll('.conversacion-item').forEach(item => {
            item.classList.remove('active');});
        const activeItem = document.querySelector(`.conversacion-item[data-conversacion-id="${conversacionId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
};


// ==========================================
// MÓDULO: UI - Interfaz de usuario
// ==========================================
const ChatUI = {
    typingIndicator: null,

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const now = new Date();
        const time = now.toLocaleTimeString('es-EC', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${text}
                <div class="message-time">${time}</div>
            </div>
        `;
        
        DOM.messagesContainer.appendChild(messageDiv);

        // ✅ RENDERIZAR FÓRMULAS CON MATHJAX
        if (sender === 'bot' && typeof MathJax !== 'undefined') {
            MathJax.typesetPromise([messageDiv]).catch((err) => console.log(err));
        }

        this.scrollToBottom();
    },


    addMessageFromData(msgData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msgData.tipo}`;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${msgData.mensaje}
                <div class="message-time">${msgData.fecha}</div>
            </div>
        `;
        
        DOM.messagesContainer.appendChild(messageDiv);

        // ✅ RENDERIZAR FÓRMULAS CON MATHJAX
        if (msgData.tipo === 'bot' && typeof MathJax !== 'undefined') {
            MathJax.typesetPromise([messageDiv]).catch((err) => console.log(err));
        }
        this.scrollToBottom();
    },

    showTypingIndicator() {
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'message bot';
        this.typingIndicator.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        DOM.messagesContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    },

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    },

    scrollToBottom() {
        DOM.messagesContainer.scrollTop = DOM.messagesContainer.scrollHeight;
    },

    clearInput() {
        DOM.input.value = '';
    },

    focusInput() {
        DOM.input.focus();
    }
};

// ==========================================
// MÓDULO: Títulos - Gestión de títulos
// ==========================================
const TitleManager = {
    updateMainTitle(nuevoTitulo) {
        const titleElement = document.querySelector('.chatbot-title');
        titleElement.classList.add('typing-title');
        titleElement.textContent = '';
        
        let i = 0;
        const typingInterval = setInterval(() => {
            if (i < nuevoTitulo.length) {
                titleElement.textContent += nuevoTitulo.charAt(i);
                i++;
            } else {
                clearInterval(typingInterval);
                titleElement.classList.remove('typing-title');
            }
        }, CONFIG.TYPING_SPEED);
    },

    updateSidebarTitle(conversacionId, nuevoTitulo) {
        const conversacionItems = document.querySelectorAll('.conversacion-item');
        
        conversacionItems.forEach(item => {
            const itemId = item.getAttribute('data-conversacion-id');
            
            if (itemId && parseInt(itemId) === conversacionId) {
                const tituloElement = item.querySelector('.conv-titulo');
                if (tituloElement) {
                    // ✅ Aplicar la misma animación de escritura
                    tituloElement.textContent = '';
                    
                    let i = 0;
                    const typingInterval = setInterval(() => {
                        if (i < nuevoTitulo.length) {
                            tituloElement.textContent += nuevoTitulo.charAt(i);
                            i++;
                        } else {
                            clearInterval(typingInterval);
                        }
                    }, CONFIG.TYPING_SPEED);
                }
            }
        });
    },

    // ✅ NUEVO MÉTODO - Actualizar ambos títulos simultáneamente
    updateBothTitles(conversacionId, nuevoTitulo) {
        // Actualizar título principal con animación
        this.updateMainTitle(nuevoTitulo);
        
        // Actualizar título del sidebar con la misma animación
        this.updateSidebarTitle(conversacionId, nuevoTitulo);
    }
};

// ==========================================
// MÓDULO: Sidebar - Gestión del sidebar
// ==========================================
const SidebarManager = {
    toggle() {
        DOM.sidebar.classList.toggle('hidden');
        DOM.menuIcon.classList.toggle('hidden');
        DOM.closeIcon.classList.toggle('hidden');
        
        this.saveState();
    },

    saveState() {
        const isHidden = DOM.sidebar.classList.contains('hidden');
        localStorage.setItem('sidebarHidden', isHidden);
    },

    restoreState() {
        const sidebarHidden = localStorage.getItem('sidebarHidden') === 'true';
        
        if (DOM.sidebar && DOM.menuIcon && DOM.closeIcon) {
            if (sidebarHidden) {
                DOM.sidebar.classList.add('hidden');
                DOM.menuIcon.classList.remove('hidden');
                DOM.closeIcon.classList.add('hidden');
            } else {
                DOM.sidebar.classList.remove('hidden');
                DOM.menuIcon.classList.add('hidden');
                DOM.closeIcon.classList.remove('hidden');
            }
        }
    }
};

// ==========================================
// MÓDULO: Conversaciones - Crear/Eliminar
// ==========================================
const ConversationManager = {
    hasMessages() {
        const messages = document.querySelectorAll('#chatbotMessages .message');
        return messages.length > 0;
    },

    async create() {
        if (!this.hasMessages()) {
            Notification.warning(
                MESSAGES.EMPTY_CONVERSATION.title,
                MESSAGES.EMPTY_CONVERSATION.message
            );
            return;
        }

        try {
            const data = await ChatAPI.createConversation();
            if (data.conversacion_id) {
                NavigationManager.addToSidebar(data);
                await NavigationManager.loadConversation(data.conversacion_id);
                Notification.success(
                    'Nueva conversación',
                    'Conversación creada correctamente',
                    2000
                );
            }
        } catch (error) {
            console.error('Error al crear conversación:', error);
            Notification.error(
                MESSAGES.CREATE_ERROR.title,
                MESSAGES.CREATE_ERROR.message
            );
        }
    },

    async delete(event, conversacionId) {
        event.preventDefault();
        event.stopPropagation();
        
        const confirmed = await Modal.show(
            MESSAGES.DELETE_CONFIRM.title,
            MESSAGES.DELETE_CONFIRM.message,
            MESSAGES.DELETE_CONFIRM.confirmText,
            true
        );

        if (!confirmed) return;

        try {
            // ✅ ANTES de eliminar, verificar cuántas conversaciones quedan
            const totalConversaciones = document.querySelectorAll('.conversacion-item').length;
            const esUltimaConversacion = totalConversaciones === 1;

            const data = await ChatAPI.deleteConversation(conversacionId);
            
            if (data.success) {
                // Remover del sidebar
                NavigationManager.removeFromSidebar(conversacionId);
                
                // ✅ Si era la última, crear una nueva automáticamente
                if (esUltimaConversacion) {
                    console.log('✨ Era la última conversación, creando una nueva...');
                    
                    // Crear nueva conversación
                    const nuevaConvData = await ChatAPI.createConversation();
                    
                    if (nuevaConvData.conversacion_id) {
                        // Agregar al sidebar
                        NavigationManager.addToSidebar(nuevaConvData);
                        
                        // Cargar la conversación
                        await NavigationManager.loadConversation(nuevaConvData.conversacion_id);
                        
                        // Notificación
                        Notification.success(
                            'Conversación eliminada',
                            'Nueva conversación creada automáticamente',
                            2000
                        );
                    }
                } else {
                    // Si no era la última, cargar la siguiente disponible
                    if (data.redirect_url) {
                        const match = data.redirect_url.match(/\/chat\/(\d+)\//);
                        
                        if (match) {
                            const newConversacionId = parseInt(match[1]);
                            await NavigationManager.loadConversation(newConversacionId);
                            
                            Notification.success(
                                MESSAGES.DELETE_SUCCESS.title,
                                MESSAGES.DELETE_SUCCESS.message,
                                2000
                            );
                        }
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error al eliminar:', error);
            Notification.error(
                MESSAGES.DELETE_ERROR.title,
                MESSAGES.DELETE_ERROR.message
            );
        }
    }
};

// ==========================================
// MÓDULO: Gestión de Insights
// ==========================================
const InsightsManager = {
    modal: null,
    
    init() {
        this.modal = document.getElementById('insightsModal');
    },
    
    abrir() {
        if (this.modal) {
            this.modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    cerrar() {
        if (this.modal) {
            this.modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    },
    
    async descartarInsight(insightId) {
        try {
            const response = await fetch(`/chatbot/insights/${insightId}/descartar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': Utils.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                // Remover visualmente
                const card = document.querySelector(`[data-insight-id="${insightId}"]`);
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'translateX(-20px)';
                    setTimeout(() => card.remove(), 300);
                }
                
                // Actualizar contador
                this.actualizarContador();
                
                Notification.success('Insight marcado', 'El insight fue marcado como visto', 2000);
            }
        } catch (error) {
            console.error('Error al descartar insight:', error);
            Notification.error('Error', 'No se pudo marcar el insight');
        }
    },
    
    async descartarTodos() {
        try {
            const response = await fetch('/chatbot/insights/descartar-todos/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': Utils.getCookie('csrftoken')
                }
            });
            
            if (response.ok) {
                // Cerrar modal y recargar
                this.cerrar();
                location.reload();
            }
        } catch (error) {
            console.error('Error al descartar todos:', error);
            Notification.error('Error', 'No se pudieron marcar los insights');
        }
    },
    
    actualizarContador() {
        const cards = document.querySelectorAll('.insight-card');
        const count = cards.length;
        
        const badge = document.querySelector('.badge-count');
        if (badge) {
            badge.textContent = count;
            
            if (count === 0) {
                this.cerrar();
                // Ocultar badge
                const btn = document.getElementById('insightsButton');
                if (btn) btn.style.display = 'none';
            }
        }
    }
};

// Funciones globales para el HTML
function abrirModalInsights() {
    InsightsManager.abrir();
}

function cerrarModalInsights(event) {
    if (!event || event.target === event.currentTarget) {
        InsightsManager.cerrar();
    }
}

function descartarInsight(id) {
    InsightsManager.descartarInsight(id);
}

function descartarTodosInsights() {
    InsightsManager.descartarTodos();
}


// ==========================================
// MÓDULO: Mensajes - Envío de mensajes
// ==========================================
const MessageHandler = {
    async send() {
        const message = DOM.input.value.trim();
        if (!message) return;

        ChatUI.addMessage(message, 'user');
        ChatUI.clearInput();
        ChatUI.showTypingIndicator();

        try {
            console.log('📤 Enviando mensaje a conversación:', window.CONVERSACION_ID); // ✅ LOG
            
            const data = await ChatAPI.sendMessage(message, window.CONVERSACION_ID);
            
            ChatUI.hideTypingIndicator();
            ChatUI.addMessage(
                data.respuesta || data.error || MESSAGES.INVALID_RESPONSE.message, 
                'bot'
            );
            
            // ✅ MARCAR que esta conversación ahora tiene mensajes
            EmptyConversationManager.markCurrentAsHavingMessages();
            
            console.log('✅ Mensaje enviado. Conversaciones con mensajes:', EmptyConversationManager.conversationsWithMessages); // ✅ LOG
            
            if (data.es_primer_mensaje && data.nuevo_titulo) {
                TitleManager.updateBothTitles(window.CONVERSACION_ID, data.nuevo_titulo);
            }
        } catch (error) {
            ChatUI.hideTypingIndicator();
            ChatUI.addMessage(MESSAGES.SERVER_ERROR.message, 'bot');
            
            Notification.error(
                MESSAGES.SERVER_ERROR.title,
                MESSAGES.SERVER_ERROR.message
            );
            
            console.error('❌ Error al enviar mensaje:', error); // ✅ LOG
        }
    }
};

// ==========================================
// MÓDULO: Reconocimiento de Voz
// ==========================================
const VoiceRecognition = {
    recognition: null,

    init() {
        if (!('webkitSpeechRecognition' in window)) {
            console.warn("Web Speech API no soportada en este navegador.");
            if (DOM.micBtn) {
                DOM.micBtn.style.display = 'none';
            }
            return;
        }

        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.lang = 'es-ES';
        this.recognition.interimResults = false;

        this.setupEventListeners();
    },

    setupEventListeners() {
        DOM.micBtn.addEventListener('click', () => {
            if (DOM.micBtn.classList.contains('listening')) {
                this.stop();
            } else {
                this.start();
            }
        });

        this.recognition.onstart = () => {
            DOM.micBtn.classList.add('listening');
            DOM.input.placeholder = "Escuchando...";
            DOM.micBtn.title = "Escuchando... clic para detener";
        };

        this.recognition.onend = () => {
            DOM.micBtn.classList.remove('listening');
            DOM.input.placeholder = "Escribe tu mensaje...";
            DOM.micBtn.title = "Hablar";
            ChatUI.focusInput();
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            DOM.input.value = transcript;
        };

        this.recognition.onerror = (event) => {
            console.error("Error de reconocimiento de voz:", event.error);
            DOM.micBtn.classList.remove('listening');
            DOM.input.placeholder = "Error al escuchar. Intenta escribir.";
        };
    },

    start() {
        this.recognition.start();
    },

    stop() {
        this.recognition.stop();
    }
};

// ==========================================
// UTILIDADES
// ==========================================
const Utils = {
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

// ==========================================
// FUNCIONES GLOBALES (Para HTML onclick)
// ==========================================
function sendMessage() {
    MessageHandler.send();
}

function toggleSidebar() {
    SidebarManager.toggle();
}

function nuevaConversacion() {
    ConversationManager.create();
}

function eliminarConversacion(event, conversacionId) {
    ConversationManager.delete(event, conversacionId);
}

// ==========================================
// EVENT LISTENERS
// ==========================================
function setupEventListeners() {
    DOM.sendBtn.addEventListener('click', sendMessage);

    DOM.input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const message = chip.getAttribute('data-message');
            DOM.input.value = message;
            sendMessage();
        });
    });
}

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    Modal.init();
    Notification.init();
    EmptyConversationManager.init(CONVERSACION_ID);
    ChatUI.scrollToBottom();
    SidebarManager.restoreState();
    VoiceRecognition.init();
    setupEventListeners();
    InsightsManager.init();

});