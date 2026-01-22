"""
Firebase Service
Notifica cambios a Firebase Realtime Database
"""

import requests
import time
import logging

logger = logging.getLogger(__name__)


class FirebaseService:
    """
    Servicio para notificar cambios en tiempo real via Firebase
    No requiere firebase-admin, usa REST API directamente
    """
    
    # ⭐ CAMBIA ESTA URL POR LA TUYA
    DATABASE_URL = "https://predictai-8f5bb-default-rtdb.firebaseio.com/"
    
    @classmethod
    def ping_update(cls, company_id='demo_company'):
        """
        Notifica a Firebase que hubo un cambio enviando timestamp actual
        
        Args:
            company_id: ID de la empresa (por ahora hardcodeado como 'demo_company')
        """
        try:
            # Timestamp en milisegundos (JavaScript usa milisegundos)
            timestamp = int(time.time() * 1000)
            
            # URL del endpoint de Firebase
            # IMPORTANTE: .json es requerido por Firebase REST API
            url = f"{cls.DATABASE_URL}/companies/{company_id}/ping.json"
            
            # PUT actualiza/crea el valor en Firebase
            response = requests.put(
                url, 
                json=timestamp,
                timeout=5  # Timeout de 5 segundos
            )
            
            if response.status_code == 200:
                logger.info(f"🔥 Firebase notificado exitosamente: {company_id} (timestamp: {timestamp})")
                return True
            else:
                logger.error(f"❌ Error en Firebase: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout al notificar Firebase (5s)")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("🌐 Error de conexión con Firebase")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de red al notificar Firebase: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado al notificar Firebase: {e}")
            return False
    
    @classmethod
    def test_connection(cls):
        """
        Prueba la conexión a Firebase
        Útil para debugging - devuelve True si la conexión es exitosa
        """
        try:
            url = f"{cls.DATABASE_URL}/.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ Conexión a Firebase exitosa")
                return True
            else:
                logger.error(f"❌ Error de conexión: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ No se pudo conectar a Firebase: {e}")
            return False
    
    @classmethod
    def get_last_ping(cls, company_id='demo_company'):
        """
        Obtiene el último ping de una empresa (útil para debugging)
        """
        try:
            url = f"{cls.DATABASE_URL}/companies/{company_id}/ping.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                timestamp = response.json()
                if timestamp:
                    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000))
                    logger.info(f"Último ping de {company_id}: {date}")
                    return timestamp
                else:
                    logger.info(f"No hay pings registrados para {company_id}")
                    return None
            else:
                logger.error(f"Error al obtener ping: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener ping: {e}")
            return None