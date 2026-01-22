/**
 * FirebaseSync
 * Gestiona la conexión y sincronización con Firebase Realtime Database
 */

class FirebaseSync {
    /**
     * @param {string} companyId - ID de la empresa a escuchar
     * @param {Function} onUpdate - Callback cuando hay cambios
     */
    constructor(companyId, onUpdate) {
        this.companyId = companyId;
        this.onUpdate = onUpdate;
        this.db = null;
        this.listener = null;
        this.isListening = false;
        
        // Inicializar Firebase al crear la instancia
        this.initializeFirebase();
    }

    /**
     * Inicializa Firebase con la configuración
     */
    initializeFirebase() {
        try {
            // ⭐ CONFIGURACIÓN DE FIREBASE (cámbiala por la tuya)
            const firebaseConfig = {
                apiKey: "AIzaSyBxKvN9X...",  // ← TU API KEY
                authDomain: "predictai-8f5bb.firebaseapp.com",
                databaseURL: "https://predictai-8f5bb-default-rtdb.firebaseio.com/",  // ← TU URL
                projectId: "predictai-8f5bb",
                storageBucket: "predictai-8f5bb.appspot.com",
                messagingSenderId: "234567890",
                appId: "1:234567890:web:abc123"
            };

            // Verificar si Firebase ya está inicializado
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
                console.log('🔥 Firebase inicializado correctamente');
            }

            // Obtener referencia a la base de datos
            this.db = firebase.database();

        } catch (error) {
            console.error('❌ Error al inicializar Firebase:', error);
        }
    }

    /**
     * Inicia el listener de Firebase
     */
    startListening() {
        if (this.isListening) {
            console.warn('🔥 Ya está escuchando Firebase');
            return;
        }

        if (!this.db) {
            console.error('❌ Firebase no está inicializado');
            return;
        }

        // Referencia al "ping" de la empresa
        const pingRef = this.db.ref(`companies/${this.companyId}/ping`);
        
        console.log(`🔊 Iniciando listener de Firebase para: ${this.companyId}`);

        // Escuchar cambios en tiempo real
        this.listener = pingRef.on('value', (snapshot) => {
            const timestamp = snapshot.val();
            
            if (timestamp) {
                const date = new Date(timestamp);
                console.log(`📡 Cambio detectado en Firebase: ${date.toLocaleString()}`);
                
                // Llamar callback para actualizar dashboard
                if (this.onUpdate) {
                    this.onUpdate();
                }
            }
        });

        this.isListening = true;
    }

    /**
     * Detiene el listener
     */
    stopListening() {
        if (this.listener && this.isListening) {
            const pingRef = this.db.ref(`companies/${this.companyId}/ping`);
            pingRef.off('value', this.listener);
            this.listener = null;
            this.isListening = false;
            console.log('🔥 Listener de Firebase detenido');
        }
    }

    /**
     * Verifica si está escuchando
     */
    isActive() {
        return this.isListening;
    }
}

export default FirebaseSync;