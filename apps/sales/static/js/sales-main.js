/**
 * sales-main.js - Orquestador principal del punto de venta
 */

import BarcodeScanner from './modules/BarcodeScanner.js';
import VoiceAssistant from './modules/VoiceAssistant.js';
import SpeechManager from './modules/SpeechManager.js';
import Carrito from './modules/Carrito.js';

class PuntoVenta {
    constructor() {
        // Módulos
        this.scanner = new BarcodeScanner();
        this.voiceAssistant = new VoiceAssistant();
        this.carrito = new Carrito();
        
        // Estado
        this.currentProduct = null;
        this.isProcessing = false;
        this.camerasLoaded = false;
        
        // DOM
        this.DOM = {
            toggleVoiceBtn: document.getElementById('toggle-voice-btn'),
            voiceStatus: document.getElementById('voice-status'),
            productInfo: document.getElementById('product-info'),
            productName: document.getElementById('product-name'),
            productCode: document.getElementById('product-code'),
            productPrice: document.getElementById('product-price'),
            productStock: document.getElementById('product-stock'),
            quantityInput: document.getElementById('quantity'),
            qtyMinus: document.getElementById('qty-minus'),
            qtyPlus: document.getElementById('qty-plus'),
            addToCartBtn: document.getElementById('add-to-cart-btn'),
            cartItems: document.getElementById('cart-items'),
            cartSubtotal: document.getElementById('cart-subtotal'),
            cartTotal: document.getElementById('cart-total'),
            clearCartBtn: document.getElementById('clear-cart-btn'),
            finalizeSaleBtn: document.getElementById('finalize-sale-btn'),
            confirmSaleBtn: document.getElementById('confirm-sale-btn'),
            modalTotal: document.getElementById('modal-total'),
            // Nuevos elementos de cámara
            cameraSelector: document.getElementById('camera-selector'),
            cameraSelectDiv: document.getElementById('camera-select-container'),
            startScannerBtn: document.getElementById('start-scanner-btn'),
            scannerStatus: document.getElementById('scanner-status')
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Inicializando Punto de Venta...');
        
        // Verificar disponibilidad de voz
        const voiceAvailable = SpeechManager.isAvailable();
        if (!voiceAvailable.full) {
            console.warn('⚠️ Funciones de voz no disponibles completamente');
            this.DOM.toggleVoiceBtn.disabled = true;
            this.DOM.toggleVoiceBtn.textContent = '🎤 Voz no disponible';
        }
        
        // Inicializar scanner (solo la instancia)
        try {
            await this.scanner.init();
            this.scanner.onProductScanned = (code) => this.handleProductScanned(code);
            
            // Cargar lista de cámaras
            await this.loadCameras();
            
        } catch (error) {
            console.error('Error al inicializar scanner:', error);
            this.showCameraError();
        }
        
        // Setup eventos
        this.setupEventListeners();
        this.setupVoiceAssistant();
        this.setupCart();
        
        console.log('✅ Punto de Venta listo');
    }

    /**
     * Cargar lista de cámaras disponibles
     */
    async loadCameras() {
        try {
            const cameras = await this.scanner.getCameras();
            
            if (cameras.length === 0) {
                throw new Error('No se encontraron cámaras');
            }
            
            // Llenar el selector
            this.DOM.cameraSelector.innerHTML = '';
            cameras.forEach((camera, index) => {
                const option = document.createElement('option');
                option.value = camera.id;
                option.textContent = camera.label;
                
                // Marcar como seleccionada la cámara trasera si existe
                if (camera.label.toLowerCase().includes('back') || 
                    camera.label.toLowerCase().includes('trasera') ||
                    camera.label.toLowerCase().includes('rear')) {
                    option.selected = true;
                }
                
                this.DOM.cameraSelector.appendChild(option);
            });
            
            this.camerasLoaded = true;
            console.log(`✅ ${cameras.length} cámara(s) disponible(s)`);
            
        } catch (error) {
            console.error('Error al cargar cámaras:', error);
            throw error;
        }
    }

    /**
     * Mostrar error de cámara
     */
    showCameraError() {
        this.DOM.cameraSelectDiv.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <strong>❌ Error al acceder a la cámara</strong><br>
                <small>Verifica los permisos del navegador o intenta con otro dispositivo.</small>
            </div>
        `;
    }

    /**
     * Iniciar scanner con la cámara seleccionada
     */
    async startScanner() {
        const selectedCameraId = this.DOM.cameraSelector.value;
        
        if (!selectedCameraId) {
            alert('Por favor selecciona una cámara');
            return;
        }
        
        try {
            // Deshabilitar botón mientras inicia
            this.DOM.startScannerBtn.disabled = true;
            this.DOM.startScannerBtn.innerHTML = '<span class="loading-spinner"></span> Iniciando...';
            
            await this.scanner.startWithCamera(selectedCameraId);
            
            // Ocultar selector y mostrar scanner
            this.DOM.cameraSelectDiv.classList.add('d-none');
            this.DOM.scannerStatus.classList.remove('d-none');
            
            // Actualizar texto del status
            const cameraName = this.DOM.cameraSelector.options[this.DOM.cameraSelector.selectedIndex].text;
            this.DOM.scannerStatus.querySelector('span').textContent = `Escaneando con: ${cameraName}`;
            
            console.log('✅ Scanner iniciado correctamente');
            
        } catch (error) {
            console.error('Error al iniciar scanner:', error);
            alert('No se pudo iniciar el scanner. Verifica los permisos de la cámara.');
            
            // Rehabilitar botón
            this.DOM.startScannerBtn.disabled = false;
            this.DOM.startScannerBtn.innerHTML = '📷 Iniciar Scanner';
        }
    }

    /**
     * Cambiar de cámara (mientras está escaneando)
     */
    async changeCamera() {
        // Mostrar selector de nuevo
        this.DOM.scannerStatus.classList.add('d-none');
        this.DOM.cameraSelectDiv.classList.remove('d-none');
        
        // Detener scanner actual
        if (this.scanner.isActive()) {
            await this.scanner.stop();
        }
        
        // Rehabilitar botón
        this.DOM.startScannerBtn.disabled = false;
        this.DOM.startScannerBtn.innerHTML = '📷 Iniciar Scanner';
    }

    setupEventListeners() {
        // Toggle voz
        this.DOM.toggleVoiceBtn.addEventListener('click', () => this.toggleVoice());
        
        // Scanner
        this.DOM.startScannerBtn.addEventListener('click', () => this.startScanner());
        document.getElementById('change-camera-btn')?.addEventListener('click', () => this.changeCamera());
        
        // Cantidad
        this.DOM.qtyMinus.addEventListener('click', () => this.adjustQuantity(-1));
        this.DOM.qtyPlus.addEventListener('click', () => this.adjustQuantity(1));
        
        // Agregar al carrito
        this.DOM.addToCartBtn.addEventListener('click', () => this.addCurrentProductToCart());
        
        // Limpiar carrito
        this.DOM.clearCartBtn.addEventListener('click', () => this.clearCart());
        
        // Finalizar venta
        this.DOM.finalizeSaleBtn.addEventListener('click', () => this.showCheckoutModal());
        this.DOM.confirmSaleBtn.addEventListener('click', () => this.confirmSale());
    }

    setupVoiceAssistant() {
        this.voiceAssistant.onCommandProcessed = (data) => {
            this.handleVoiceCommand(data);
        };
    }

    setupCart() {
        this.carrito.onCartUpdate = (carrito) => {
            this.renderCart();
        };
    }

    async toggleVoice() {
        if (this.voiceAssistant.isEnabled()) {
            await this.voiceAssistant.deactivate();
            this.DOM.toggleVoiceBtn.textContent = '🎤 Activar Asistente de Voz';
            this.DOM.toggleVoiceBtn.classList.remove('btn-danger');
            this.DOM.toggleVoiceBtn.classList.add('btn-primary');
            this.DOM.voiceStatus.classList.add('d-none');
        } else {
            const activated = await this.voiceAssistant.activate();
            if (activated) {
                this.DOM.toggleVoiceBtn.textContent = '🔴 Desactivar Voz';
                this.DOM.toggleVoiceBtn.classList.remove('btn-primary');
                this.DOM.toggleVoiceBtn.classList.add('btn-danger');
                this.DOM.voiceStatus.classList.remove('d-none');
            }
        }
    }

    async handleProductScanned(code) {
        if (this.isProcessing) {
            return;
        }
        
        this.isProcessing = true;
        console.log('🔍 Buscando producto:', code);
        
        await this.scanner.pause();
        
        try {
            const response = await fetch(`/sales/api/producto/${code}/`);
            
            if (!response.ok) {
                throw new Error('Producto no encontrado');
            }
            
            const data = await response.json();
            
            if (data.encontrado) {
                this.currentProduct = data.producto;
                this.showProductInfo();
                
                if (this.voiceAssistant.isEnabled()) {
                    const message = `${this.currentProduct.nombre} detectado. Precio: ${this.currentProduct.precio_venta} dólares. ¿Cuántos deseas agregar?`;
                    await this.voiceAssistant.speak(message);
                    this.voiceAssistant.addToConversationLog(message, 'bot');
                    
                    this.voiceAssistant.updateContext({
                        producto_actual: this.currentProduct.nombre,
                        precio_actual: this.currentProduct.precio_venta,
                        total_parcial: this.carrito.getTotal(),
                        items_en_carrito: this.carrito.getItemCount()
                    });
                }
            }
            
        } catch (error) {
            console.error('Error buscando producto:', error);
            
            if (this.voiceAssistant.isEnabled()) {
                await this.voiceAssistant.speak('Producto no encontrado. Escanea otro código.');
            }
            
            this.showNotification('Producto no encontrado', 'error');
        } finally {
            this.isProcessing = false;
            
            setTimeout(() => {
                this.scanner.resume();
            }, 1500);
        }
    }

    showProductInfo() {
        this.DOM.productName.textContent = this.currentProduct.nombre;
        this.DOM.productCode.textContent = this.currentProduct.codigo_barras;
        this.DOM.productPrice.textContent = this.currentProduct.precio_venta.toFixed(2);
        this.DOM.productStock.textContent = this.currentProduct.stock;
        this.DOM.quantityInput.value = 1;
        this.DOM.quantityInput.max = this.currentProduct.stock;
        
        this.DOM.productInfo.classList.remove('d-none');
        
        if (this.currentProduct.stock <= 0) {
            this.DOM.addToCartBtn.disabled = true;
            this.DOM.addToCartBtn.textContent = '❌ Sin Stock';
        } else {
            this.DOM.addToCartBtn.disabled = false;
            this.DOM.addToCartBtn.textContent = '➕ Agregar al Carrito';
        }
    }

    adjustQuantity(delta) {
        let current = parseInt(this.DOM.quantityInput.value);
        let newValue = current + delta;
        
        if (newValue >= 1 && newValue <= this.currentProduct.stock) {
            this.DOM.quantityInput.value = newValue;
        }
    }

    async addCurrentProductToCart() {
        if (!this.currentProduct) {
            return;
        }
        
        const cantidad = parseInt(this.DOM.quantityInput.value);
        
        if (cantidad <= 0 || cantidad > this.currentProduct.stock) {
            this.showNotification('Cantidad inválida', 'error');
            return;
        }
        
        const totalParcial = this.carrito.addItem(this.currentProduct, cantidad);
        
        this.DOM.productInfo.classList.add('d-none');
        this.currentProduct = null;
        
        if (this.voiceAssistant.isEnabled()) {
            const message = `${cantidad} agregados. Total parcial: ${totalParcial.toFixed(2)} dólares. Escanea otro producto o di terminar venta.`;
            await this.voiceAssistant.speak(message);
            this.voiceAssistant.addToConversationLog(message, 'bot');
            
            this.voiceAssistant.updateContext({
                producto_actual: null,
                total_parcial: totalParcial,
                items_en_carrito: this.carrito.getItemCount()
            });
        }
        
        this.showNotification('Producto agregado', 'success');
    }

    async handleVoiceCommand(data) {
        const { accion, cantidad, confirmacion } = data;
        
        switch (accion) {
            case 'agregar_cantidad':
                if (this.currentProduct && cantidad) {
                    this.DOM.quantityInput.value = cantidad;
                    await this.addCurrentProductToCart();
                }
                break;
                
            case 'confirmar_venta':
                if (confirmacion) {
                    await this.confirmSale();
                }
                break;
                
            case 'cancelar_venta':
                this.clearCart();
                await this.voiceAssistant.speak('Venta cancelada');
                break;
                
            case 'eliminar_ultimo':
                const removed = this.carrito.removeLastItem();
                if (removed) {
                    await this.voiceAssistant.speak(`${removed.nombre} eliminado del carrito`);
                }
                break;
                
            case 'consultar_total':
                const total = this.carrito.getTotal();
                const itemCount = this.carrito.getItemCount();
                await this.voiceAssistant.speak(`Total actual: ${total.toFixed(2)} dólares con ${itemCount} productos`);
                break;
        }
    }

    renderCart() {
        const items = this.carrito.getItems();
        
        if (items.length === 0) {
            this.DOM.cartItems.innerHTML = '<p class="text-muted text-center">El carrito está vacío</p>';
            this.DOM.finalizeSaleBtn.disabled = true;
        } else {
            let html = '';
            items.forEach((item, index) => {
                const subtotal = item.precio * item.cantidad;
                html += `
                    <div class="cart-item">
                        <div class="item-info">
                            <strong>${item.nombre}</strong>
                            <small class="text-muted">$${item.precio.toFixed(2)} × ${item.cantidad}</small>
                        </div>
                        <div class="item-actions">
                            <span class="item-subtotal">$${subtotal.toFixed(2)}</span>
                            <button class="btn btn-sm btn-outline-danger" onclick="puntoVenta.removeCartItem(${index})">
                                ✕
                            </button>
                        </div>
                    </div>
                `;
            });
            
            this.DOM.cartItems.innerHTML = html;
            this.DOM.finalizeSaleBtn.disabled = false;
        }
        
        const subtotal = this.carrito.getSubtotal();
        const total = this.carrito.getTotal();
        
        this.DOM.cartSubtotal.textContent = subtotal.toFixed(2);
        this.DOM.cartTotal.textContent = total.toFixed(2);
    }

    removeCartItem(index) {
        this.carrito.removeItem(index);
    }

    clearCart() {
        if (confirm('¿Limpiar todo el carrito?')) {
            this.carrito.clear();
            this.voiceAssistant.clearContext();
        }
    }

    async showCheckoutModal() {
        const total = this.carrito.getTotal();
        const itemCount = this.carrito.getItemCount();
        
        this.DOM.modalTotal.textContent = total.toFixed(2);
        
        if (this.voiceAssistant.isEnabled()) {
            const message = `Total: ${total.toFixed(2)} dólares con ${itemCount} productos. ¿Confirmas la venta?`;
            await this.voiceAssistant.speak(message);
            this.voiceAssistant.addToConversationLog(message, 'bot');
        }
        
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        modal.show();
    }

    async confirmSale() {
        const items = this.carrito.prepareForCheckout();
        
        if (items.length === 0) {
            return;
        }
        
        try {
            const response = await fetch('/sales/api/venta/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    items: items,
                    usa_voz: this.voiceAssistant.isEnabled(),
                    dispositivo: 'Web'
                })
            });
            
            if (!response.ok) {
                throw new Error('Error al procesar la venta');
            }
            
            const data = await response.json();
            
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('confirmModal')).hide();
                
                if (this.voiceAssistant.isEnabled()) {
                    await this.voiceAssistant.speak(`Venta confirmada por ${data.total.toFixed(2)} dólares. ¡Gracias!`);
                }
                
                this.showNotification(`✅ Venta #${data.venta_id} registrada: $${data.total.toFixed(2)}`, 'success');
                
                this.carrito.clear();
                this.voiceAssistant.clearContext();
                this.DOM.productInfo.classList.add('d-none');
                
            } else {
                throw new Error(data.mensaje || 'Error desconocido');
            }
            
        } catch (error) {
            console.error('Error confirmando venta:', error);
            this.showNotification('Error al procesar la venta', 'error');
        }
    }

    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

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
}

let puntoVenta;

document.addEventListener('DOMContentLoaded', () => {
    puntoVenta = new PuntoVenta();
    window.puntoVenta = puntoVenta;
});