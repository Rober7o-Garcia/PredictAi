/**
 * Carrito - Gestión del carrito de compras
 */

class Carrito {
    constructor() {
        this.items = [];
        this.onCartUpdate = null; // Callback
    }

    /**
     * Agregar producto
     */
    addItem(producto, cantidad = 1) {
        // Verificar si ya existe
        const existente = this.items.find(item => item.producto_id === producto.id);
        
        if (existente) {
            existente.cantidad += cantidad;
        } else {
            this.items.push({
                producto_id: producto.id,
                nombre: producto.nombre,
                precio: parseFloat(producto.precio_venta),
                cantidad: cantidad,
                codigo_barras: producto.codigo_barras
            });
        }
        
        console.log(`✅ Agregado: ${cantidad}x ${producto.nombre}`);
        this.notifyUpdate();
        
        return this.getTotal();
    }

    /**
     * Quitar item por índice
     */
    removeItem(index) {
        if (index >= 0 && index < this.items.length) {
            const item = this.items[index];
            this.items.splice(index, 1);
            console.log(`🗑️ Eliminado: ${item.nombre}`);
            this.notifyUpdate();
        }
    }

    /**
     * Quitar último item
     */
    removeLastItem() {
        if (this.items.length > 0) {
            const item = this.items.pop();
            console.log(`🗑️ Eliminado último: ${item.nombre}`);
            this.notifyUpdate();
            return item;
        }
        return null;
    }

    /**
     * Actualizar cantidad de un item
     */
    updateQuantity(index, newQuantity) {
        if (index >= 0 && index < this.items.length && newQuantity > 0) {
            this.items[index].cantidad = newQuantity;
            this.notifyUpdate();
        }
    }

    /**
     * Limpiar carrito
     */
    clear() {
        this.items = [];
        console.log('🗑️ Carrito limpiado');
        this.notifyUpdate();
    }

    /**
     * Obtener items
     */
    getItems() {
        return [...this.items];
    }

    /**
     * Calcular subtotal
     */
    getSubtotal() {
        return this.items.reduce((sum, item) => {
            return sum + (item.precio * item.cantidad);
        }, 0);
    }

    /**
     * Calcular total (por ahora igual al subtotal)
     */
    getTotal() {
        return this.getSubtotal();
    }

    /**
     * Obtener cantidad de items
     */
    getItemCount() {
        return this.items.reduce((sum, item) => sum + item.cantidad, 0);
    }

    /**
     * Verificar si está vacío
     */
    isEmpty() {
        return this.items.length === 0;
    }

    /**
     * Preparar datos para enviar al backend
     */
    prepareForCheckout() {
        return this.items.map(item => ({
            producto_id: item.producto_id,
            cantidad: item.cantidad
        }));
    }

    /**
     * Notificar cambios
     */
    notifyUpdate() {
        if (this.onCartUpdate) {
            this.onCartUpdate(this);
        }
    }
}

export default Carrito;