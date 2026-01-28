/**
 * VoiceAssistant - Asistente de voz integrado con chatbot
 */

import SpeechManager from './SpeechManager.js';

class VoiceAssistant {
    constructor() {
        this.speechManager = new SpeechManager();
        this.isActive = false;
        this.currentContext = {};
        
        // Callbacks
        this.onCommandProcessed = null;
        
        // Setup
        this.setupSpeechHandler();
    }

    /**
     * Configurar manejador de voz
     */
    setupSpeechHandler() {
        this.speechManager.onSpeechDetected = (text) => {
            this.processVoiceCommand(text);
        };
    }

    /**
     * Activar asistente
     */
    async activate() {
        if (this.isActive) {
            return;
        }

        const started = this.speechManager.startListening();
        
        if (started) {
            this.isActive = true;
            await this.speak('Asistente activado. Estoy listo para ayudarte.');
            console.log('✅ Asistente de voz activado');
            return true;
        }
        
        return false;
    }

    /**
     * Desactivar asistente
     */
    async deactivate() {
        if (!this.isActive) {
            return;
        }

        this.speechManager.stopListening();
        this.speechManager.stopSpeaking();
        this.isActive = false;
        
        console.log('🔇 Asistente de voz desactivado');
    }

    /**
     * Procesar comando de voz
     */
    async processVoiceCommand(text) {
        console.log('🎤 Procesando comando:', text);
        
        // Añadir al log visual
        this.addToConversationLog(text, 'user');
        
        try {
            // Enviar al backend para interpretación
            const response = await fetch('/sales/api/comando-voz/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    texto: text,
                    contexto: this.currentContext
                })
            });

            if (!response.ok) {
                throw new Error('Error en la API');
            }

            const data = await response.json();
            
            // Responder al usuario
            await this.speak(data.respuesta_chatbot);
            this.addToConversationLog(data.respuesta_chatbot, 'bot');
            
            // Ejecutar callback con la acción
            if (this.onCommandProcessed) {
                this.onCommandProcessed(data);
            }
            
        } catch (error) {
            console.error('Error procesando comando:', error);
            await this.speak('Disculpa, hubo un error. Intenta de nuevo.');
        }
    }

    /**
     * Hablar (con el asistente)
     */
    async speak(text) {
        try {
            await this.speechManager.speak(text);
        } catch (error) {
            console.error('Error al hablar:', error);
        }
    }

    /**
     * Actualizar contexto
     */
    updateContext(newContext) {
        this.currentContext = { ...this.currentContext, ...newContext };
        console.log('📝 Contexto actualizado:', this.currentContext);
    }

    /**
     * Limpiar contexto
     */
    clearContext() {
        this.currentContext = {};
    }

    /**
     * Agregar al log de conversación
     */
    addToConversationLog(text, sender) {
        const logContainer = document.getElementById('conversation-log');
        
        if (!logContainer) return;
        
        // Limpiar mensaje inicial si existe
        if (logContainer.querySelector('.text-muted')) {
            logContainer.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `conversation-message ${sender}`;
        
        const time = new Date().toLocaleTimeString('es-EC', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <p>${text}</p>
                <span class="message-time">${time}</span>
            </div>
        `;
        
        logContainer.appendChild(messageDiv);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    /**
     * Helper para obtener CSRF token
     */
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Verificar si está activo
     */
    isEnabled() {
        return this.isActive;
    }
}

export default VoiceAssistant;