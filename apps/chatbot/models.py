from django.db import models

class Conversacion(models.Model):
    """Conversaciones separadas del chatbot"""
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200, default="Nueva conversación")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_actualizacion']
        verbose_name_plural = "Conversaciones"
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_creacion.strftime('%d/%m/%Y')}"
    
    def generar_titulo_automatico(self):
        """Genera título basado en el primer mensaje"""
        primer_mensaje = self.mensajes.filter(tipo='user').first()
        if primer_mensaje:
            # Tomar primeras 50 caracteres
            self.titulo = primer_mensaje.mensaje[:50]
            if len(primer_mensaje.mensaje) > 50:
                self.titulo += "..."
            self.save()


class MensajeChat(models.Model):
    """Historial de mensajes del chatbot"""
    TIPO_CHOICES = [
        ('user', 'Usuario'),
        ('bot', 'Bot'),
    ]
    
    conversacion = models.ForeignKey(
        Conversacion, 
        on_delete=models.CASCADE, 
        related_name='mensajes'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fecha']
        verbose_name_plural = "Mensajes del Chat"
    
    def __str__(self):
        return f"{self.tipo} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
    
    
class ConocimientoNegocio(models.Model):
    """
    Memoria persistente del chatbot sobre el negocio
    """
    TIPO_CHOICES = [
        ('meta', 'Meta/Objetivo'),
        ('preferencia', 'Preferencia'),
        ('dato_clave', 'Dato Clave'),
        ('patron', 'Patrón Detectado'),
        ('estrategia', 'Estrategia Definida'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    clave = models.CharField(max_length=200, db_index=True)  # ej: "meta_mensual", "producto_estrella"
    valor = models.TextField()  # El valor en formato JSON o texto
    contexto = models.TextField(blank=True, null=True)  # Contexto adicional
    confianza = models.FloatField(default=1.0)  # 0.0 a 1.0 - qué tan seguro está
    
    aprendido_en = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'gameplay_conocimiento_negocio'
        ordering = ['-ultima_actualizacion']
        unique_together = ['clave']  # Solo una entrada por clave
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.clave} = {self.valor[:50]}"
    

class InsightNegocio(models.Model):
    """
    Insights y patrones detectados automáticamente por el sistema
    """
    TIPO_CHOICES = [
        ('tendencia_alza', 'Tendencia al Alza'),
        ('tendencia_baja', 'Tendencia a la Baja'),
        ('correlacion', 'Correlación entre Productos'),
        ('anomalia', 'Anomalía Detectada'),
        ('oportunidad', 'Oportunidad de Negocio'),
        ('alerta', 'Alerta Importante'),
        ('estacionalidad', 'Patrón Estacional'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    severidad = models.CharField(max_length=10, choices=SEVERIDAD_CHOICES, default='media')
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    recomendacion = models.TextField(blank=True)
    
    # Datos relacionados
    producto_relacionado = models.CharField(max_length=200, blank=True, null=True)
    metrica_valor = models.FloatField(blank=True, null=True)  # ej: -30 para caída del 30%
    
    # Metadata
    detectado_en = models.DateTimeField(auto_now_add=True)
    visto = models.BooleanField(default=False)  # Si el usuario ya lo vio
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'gameplay_insight_negocio'
        ordering = ['-detectado_en']
    
    def __str__(self):
        return f"[{self.get_severidad_display()}] {self.titulo}"