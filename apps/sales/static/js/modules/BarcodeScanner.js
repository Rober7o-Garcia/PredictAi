/**
 * BarcodeScanner - ULTRA-RÁPIDO
 * Optimizado al máximo para velocidad
 */

class BarcodeScanner {
    constructor() {
        this.isScanning = false;
        this.lastScannedCode = null;
        this.lastScanTime = 0;
        this.debounceTime = 500; // ⚡ Reducido de 1500 a 800ms
        this.onProductScanned = null;
        this.availableCameras = [];
        this.selectedCameraId = null;
        this.consecutiveScans = {};
        this.minConsecutiveScans = 1; // ⚡ Reducido de 2 a 1 para respuesta instantánea
        this.detectionBuffer = []; // Buffer para validación rápida
        this.bufferSize = 2; // ⚡ Requiere 3 detecciones en 300ms
        
        // ⚡ CONFIGURACIÓN ULTRA-OPTIMIZADA
        this.config = {
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector('#barcode-reader'),
                constraints: {
                    // ⚡ Resolución optimizada para velocidad
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    aspectRatio: 1.777778,
                    facingMode: "environment",
                    // ⚡ FPS alto para detección rápida
                    frameRate: { ideal: 60, min: 30 }
                },
                // ⚡ Área de escaneo MUY reducida (solo el centro)
                area: {
                    top: "30%",
                    right: "15%",
                    left: "15%",
                    bottom: "30%"
                },
                singleChannel: false // RGB completo para mejor detección
            },
            
            // ⚡ Localizador ultra-rápido
            locator: {
                patchSize: "x-small", // ⚡ El más pequeño = más rápido
                halfSample: true // ⚡ Procesar a mitad de resolución (2x velocidad)
            },
            
            // ⚡ Máximos workers disponibles
            numOfWorkers: Math.min(navigator.hardwareConcurrency || 4, 8),
            
            // ⚡ Frecuencia máxima de escaneo
            frequency: 20, // ⚡ Aumentado de 10 a 20 intentos/segundo
            
            decoder: {
                // ⚡ SOLO lectores esenciales (menos = más rápido)
                readers: [
                    "ean_reader", // Solo EAN (incluye EAN-13, EAN-8)
                    // Comentados para máxima velocidad:
                    "code_128_reader",
                    "upc_reader"
                ],
                debug: {
                    drawBoundingBox: false, // ⚡ Desactivado para velocidad
                    showFrequency: false,
                    drawScanline: false, // ⚡ Desactivado para velocidad
                    showPattern: false
                },
                multiple: false
            },
            
            locate: true // Mantener para buena detección
        };
    }

    /**
     * Obtener cámaras disponibles
     */
    async getCameras() {
        try {
            console.log('📷 Solicitando acceso a la cámara...');
            
            let stream = null;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: "environment",
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    } 
                });
                console.log('✅ Permisos de cámara concedidos');
            } catch (permissionError) {
                console.error('❌ Permisos denegados:', permissionError);
                throw new Error('Permisos de cámara denegados. Por favor, permite el acceso.');
            }
            
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            
            if (videoDevices.length === 0) {
                throw new Error('No se encontraron cámaras disponibles');
            }
            
            this.availableCameras = videoDevices.map((device, index) => {
                let label = device.label || `Cámara ${index + 1}`;
                
                if (label.toLowerCase().includes('back') || label.toLowerCase().includes('rear')) {
                    label = `📷 ${label} (Trasera)`;
                } else if (label.toLowerCase().includes('front') || label.toLowerCase().includes('facing')) {
                    label = `🤳 ${label} (Frontal)`;
                } else {
                    label = `📹 ${label}`;
                }
                
                return {
                    id: device.deviceId,
                    label: label
                };
            });
            
            console.log('✅ Cámaras encontradas:', this.availableCameras);
            return this.availableCameras;
            
        } catch (error) {
            console.error('❌ Error al obtener cámaras:', error);
            
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                throw new Error('Permisos de cámara denegados.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No se encontró ninguna cámara.');
            } else if (error.name === 'NotReadableError') {
                throw new Error('La cámara está siendo usada por otra aplicación.');
            } else {
                throw error;
            }
        }
    }

    async init() {
        console.log('✅ Scanner QuaggaJS Ultra-Rápido inicializado');
        return true;
    }

    /**
     * Iniciar escaneo ultra-rápido
     */
    async startWithCamera(cameraId) {
        if (this.isScanning) {
            console.warn('Scanner ya está activo');
            return;
        }

        this.selectedCameraId = cameraId;
        this.config.inputStream.constraints.deviceId = { exact: cameraId };

        return new Promise((resolve, reject) => {
            Quagga.init(this.config, (err) => {
                if (err) {
                    console.error('❌ Error al inicializar Quagga:', err);
                    reject(err);
                    return;
                }
                
                console.log('✅ Quagga inicializado - Modo ULTRA-RÁPIDO');
                
                // ⚡ Configurar detector con validación en buffer
                Quagga.onDetected((result) => {
                    this.handleScanFast(result);
                });
                
                Quagga.start();
                this.isScanning = true;
                
                console.log('⚡ Scanner ULTRA-RÁPIDO activo');
                resolve();
            });
        });
    }

    /**
     * ⚡ Manejo ULTRA-RÁPIDO de código detectado
     */
    handleScanFast(result) {
        const code = result.codeResult.code;
        const now = Date.now();
        
        // ⚡ Validación rápida por confianza
        const errors = result.codeResult.decodedCodes.filter(dc => dc.error !== undefined);
        const avgError = errors.reduce((sum, dc) => sum + dc.error, 0) / errors.length;
        
        // Si el error promedio es muy alto, descartar
        if (avgError > 0.15) {
            return;
        }
        
        // ⚡ Sistema de buffer: acumular detecciones rápidas
        this.detectionBuffer.push({ code, time: now });
        
        // Limpiar buffer antiguo (solo últimos 300ms)
        this.detectionBuffer = this.detectionBuffer.filter(
            detection => (now - detection.time) < 300
        );
        
        // Contar cuántas veces apareció este código en el buffer
        const codeCount = this.detectionBuffer.filter(d => d.code === code).length;
        
        // ⚡ Si apareció suficientes veces en 300ms, es válido
        if (codeCount < this.bufferSize) {
            return;
        }
        
        // ⚡ Debounce ultra-corto
        if (code === this.lastScannedCode && (now - this.lastScanTime) < this.debounceTime) {
            return;
        }
        
        // ⚡ CÓDIGO VÁLIDO - PROCESAR INMEDIATAMENTE
        this.lastScannedCode = code;
        this.lastScanTime = now;
        this.detectionBuffer = []; // Limpiar buffer
        
        console.log('⚡ CÓDIGO ESCANEADO:', code);
        
        // ⚡ Feedback instantáneo
        this.showScanFeedback();
        this.playBeepFast();
        
        // Callback
        if (this.onProductScanned) {
            this.onProductScanned(code);
        }
    }

    /**
     * ⚡ Feedback visual ultra-rápido
     */
    showScanFeedback() {
        const overlay = document.querySelector('.scanner-overlay');
        if (overlay) {
            overlay.classList.add('scan-success');
            // ⚡ Animación más corta (200ms)
            setTimeout(() => {
                overlay.classList.remove('scan-success');
            }, 200);
        }
        
        // ⚡ Flash verde en toda la pantalla
        const flash = document.createElement('div');
        flash.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(16, 185, 129, 0.3);
            pointer-events: none;
            z-index: 9999;
            animation: flashFade 200ms ease-out;
        `;
        document.body.appendChild(flash);
        setTimeout(() => flash.remove(), 200);
    }

    /**
     * ⚡ Beep ultra-corto y agudo
     */
    playBeepFast() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // ⚡ Sonido más agudo y corto
            oscillator.frequency.value = 1200; // Más alto = más rápido de percibir
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.4, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.06);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.06); // ⚡ Más corto
        } catch (error) {
            console.warn('No se pudo reproducir beep');
        }
    }

    async pause() {
        if (this.isScanning) {
            Quagga.pause();
            console.log('⏸️ Scanner pausado');
        }
    }

    async resume() {
        if (this.isScanning) {
            Quagga.start();
            console.log('▶️ Scanner reanudado');
        }
    }

    async stop() {
        if (this.isScanning) {
            Quagga.stop();
            Quagga.offDetected();
            this.isScanning = false;
            this.selectedCameraId = null;
            this.detectionBuffer = [];
            console.log('🛑 Scanner detenido');
        }
    }

    async switchCamera(cameraId) {
        if (this.isScanning) {
            await this.stop();
        }
        await this.startWithCamera(cameraId);
    }

    isActive() {
        return this.isScanning;
    }

    getCurrentCamera() {
        return this.selectedCameraId;
    }
}

export default BarcodeScanner;