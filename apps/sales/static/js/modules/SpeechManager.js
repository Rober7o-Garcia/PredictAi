/**
 * SpeechManager - Gestiona reconocimiento y síntesis de voz
 * Compatible con navegadores modernos
 */

class SpeechManager {
    constructor() {
        // Speech Recognition (escuchar)
        this.recognition = null;
        this.isListening = false;
        this.onSpeechDetected = null;
        
        // Speech Synthesis (hablar)
        this.synthesis = window.speechSynthesis;
        this.isSpeaking = false;
        
        this.setupRecognition();
    }

    /**
     * Configurar reconocimiento de voz
     */
    setupRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.error('❌ Speech Recognition no soportado');
            return false;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true; // Escuchar continuamente
        this.recognition.interimResults = false; // Solo resultados finales
        this.recognition.lang = 'es-EC'; // Español Ecuador
        this.recognition.maxAlternatives = 1;

        // Eventos
        this.recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const text = event.results[last][0].transcript.trim();
            
            console.log('🎤 Texto detectado:', text);
            
            if (this.onSpeechDetected) {
                this.onSpeechDetected(text);
            }
        };

        this.recognition.onerror = (event) => {
            console.error('Error en reconocimiento de voz:', event.error);
            
            // Reintentar si es un error temporal
            if (event.error === 'no-speech' || event.error === 'audio-capture') {
                setTimeout(() => {
                    if (this.isListening) {
                        this.startListening();
                    }
                }, 1000);
            }
        };

        this.recognition.onend = () => {
            // Reiniciar si se supone que debe seguir escuchando
            if (this.isListening) {
                this.recognition.start();
            }
        };

        return true;
    }

    /**
     * Iniciar escucha
     */
    startListening() {
        if (!this.recognition) {
            console.error('Recognition no disponible');
            return false;
        }

        if (this.isListening) {
            console.warn('Ya está escuchando');
            return false;
        }

        try {
            this.recognition.start();
            this.isListening = true;
            console.log('🎤 Escuchando...');
            return true;
        } catch (error) {
            console.error('Error al iniciar escucha:', error);
            return false;
        }
    }

    /**
     * Detener escucha
     */
    stopListening() {
        if (!this.isListening) {
            return;
        }

        this.isListening = false;
        
        if (this.recognition) {
            this.recognition.stop();
            console.log('🔇 Dejó de escuchar');
        }
    }

    /**
     * Hablar (text-to-speech)
     */
    speak(text, options = {}) {
        return new Promise((resolve, reject) => {
            if (!this.synthesis) {
                console.error('Speech Synthesis no disponible');
                reject(new Error('Speech Synthesis no disponible'));
                return;
            }

            // Cancelar cualquier speech anterior
            this.synthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            
            // Configuración
            utterance.lang = options.lang || 'es-EC';
            utterance.rate = options.rate || 1.0; // Velocidad
            utterance.pitch = options.pitch || 1.0; // Tono
            utterance.volume = options.volume || 1.0; // Volumen

            // Buscar voz en español
            const voices = this.synthesis.getVoices();
            const spanishVoice = voices.find(v => v.lang.startsWith('es'));
            if (spanishVoice) {
                utterance.voice = spanishVoice;
            }

            utterance.onstart = () => {
                this.isSpeaking = true;
                console.log('🗣️ Hablando:', text);
            };

            utterance.onend = () => {
                this.isSpeaking = false;
                console.log('✅ Terminó de hablar');
                resolve();
            };

            utterance.onerror = (event) => {
                this.isSpeaking = false;
                console.error('Error en speech:', event);
                reject(event);
            };

            this.synthesis.speak(utterance);
        });
    }

    /**
     * Detener habla
     */
    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
            this.isSpeaking = false;
        }
    }

    /**
     * Verificar si está hablando
     */
    isTalking() {
        return this.isSpeaking;
    }

    /**
     * Verificar disponibilidad
     */
    static isAvailable() {
        const hasRecognition = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
        const hasSynthesis = !!window.speechSynthesis;
        
        return {
            recognition: hasRecognition,
            synthesis: hasSynthesis,
            full: hasRecognition && hasSynthesis
        };
    }
}

export default SpeechManager;