/**
 * BarcodeScanner - Módulo para escaneo de códigos de barras
 * Con selector de cámara para elegir manualmente
 */

class BarcodeScanner {
    constructor() {
        this.html5QrCode = null;
        this.isScanning = false;
        this.lastScannedCode = null;
        this.lastScanTime = 0;
        this.debounceTime = 2000;
        this.onProductScanned = null;
        this.availableCameras = [];
        this.selectedCameraId = null;
        
        // Configuración optimizada
        this.config = {
            fps: 10,
            qrbox: { width: 250, height: 150 },
            aspectRatio: 1.777778,
            formatsToSupport: [
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.UPC_E,
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.CODE_39
            ],
            rememberLastUsedCamera: true,
            supportedScanTypes: [Html5QrcodeScanType.SCAN_TYPE_CAMERA]
        };
    }

    /**
     * Obtener lista de cámaras disponibles
     */
    async getCameras() {
        try {
            const cameras = await Html5Qrcode.getCameras();
            
            if (!cameras || cameras.length === 0) {
                throw new Error('No se encontraron cámaras');
            }
            
            this.availableCameras = cameras.map(camera => ({
                id: camera.id,
                label: camera.label || `Cámara ${cameras.indexOf(camera) + 1}`
            }));
            
            console.log('📷 Cámaras disponibles:', this.availableCameras);
            
            return this.availableCameras;
            
        } catch (error) {
            console.error('❌ Error al obtener cámaras:', error);
            throw error;
        }
    }

    /**
     * Inicializar el scanner (crear instancia)
     */
    async init(containerId = 'barcode-reader') {
        try {
            this.html5QrCode = new Html5Qrcode(containerId);
            console.log('✅ Scanner inicializado');
            return true;
        } catch (error) {
            console.error('❌ Error al inicializar scanner:', error);
            throw error;
        }
    }

    /**
     * Iniciar escaneo con cámara específica
     */
    async startWithCamera(cameraId) {
        if (this.isScanning) {
            console.warn('Scanner ya está activo');
            return;
        }

        if (!this.html5QrCode) {
            throw new Error('Scanner no inicializado. Llama a init() primero.');
        }

        this.selectedCameraId = cameraId;

        try {
            await this.html5QrCode.start(
                cameraId,
                this.config,
                (decodedText, decodedResult) => {
                    this.handleScan(decodedText, decodedResult);
                },
                (errorMessage) => {
                    // Errores silenciosos mientras busca
                }
            );
            
            this.isScanning = true;
            console.log('📷 Scanner activo con cámara:', cameraId);
            
        } catch (error) {
            console.error('Error al iniciar scanner:', error);
            throw error;
        }
    }

    /**
     * Manejar código escaneado
     */
    handleScan(code, result) {
        const now = Date.now();
        
        // Debounce
        if (code === this.lastScannedCode && (now - this.lastScanTime) < this.debounceTime) {
            return;
        }
        
        this.lastScannedCode = code;
        this.lastScanTime = now;
        
        console.log('📷 Código escaneado:', code);
        
        // Feedback visual
        this.showScanFeedback();
        
        // Callback
        if (this.onProductScanned) {
            this.onProductScanned(code);
        }
    }

    /**
     * Feedback visual de escaneo exitoso
     */
    showScanFeedback() {
        const overlay = document.querySelector('.scanner-overlay');
        if (overlay) {
            overlay.classList.add('scan-success');
            setTimeout(() => {
                overlay.classList.remove('scan-success');
            }, 500);
        }
    }

    /**
     * Pausar scanner
     */
    async pause() {
        if (this.html5QrCode && this.isScanning) {
            await this.html5QrCode.pause();
            console.log('⏸️ Scanner pausado');
        }
    }

    /**
     * Reanudar scanner
     */
    async resume() {
        if (this.html5QrCode && this.isScanning) {
            await this.html5QrCode.resume();
            console.log('▶️ Scanner reanudado');
        }
    }

    /**
     * Detener scanner completamente
     */
    async stop() {
        if (this.html5QrCode && this.isScanning) {
            try {
                await this.html5QrCode.stop();
                this.isScanning = false;
                this.selectedCameraId = null;
                console.log('🛑 Scanner detenido');
            } catch (error) {
                console.error('Error al detener scanner:', error);
            }
        }
    }

    /**
     * Cambiar de cámara (detiene y reinicia)
     */
    async switchCamera(cameraId) {
        if (this.isScanning) {
            await this.stop();
        }
        await this.startWithCamera(cameraId);
    }

    /**
     * Verificar si está escaneando
     */
    isActive() {
        return this.isScanning;
    }

    /**
     * Obtener cámara actual
     */
    getCurrentCamera() {
        return this.selectedCameraId;
    }
}

export default BarcodeScanner;