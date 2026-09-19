from django.db import models
from django.conf import settings

# 1. Tabla Principal: El encabezado del problema
class TicketSoporte(models.Model):
    CATEGORIAS = [
        ('Pago', 'Problema de Pago'),
        ('Toxicidad', 'Comportamiento Tóxico'),
        ('Disputa', 'Disputa de Resultado'),
        ('Otro', 'Otro'),
    ]
    
    ESTADOS = [
        ('Abierto', 'Abierto'),
        ('En Revision', 'En Revisión'),
        ('Resuelto', 'Resuelto'),
        ('Cerrado', 'Cerrado'),
    ]

    # Identifica qué jugador creó el ticket pidiendo ayuda
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets_creados')
    
    # Si el problema es una disputa, conectamos el ticket con la partida conflictiva (Opcional)
    partida = models.ForeignKey('torneos.Partida', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_disputa')
    
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Abierto')
    
    # Django llenará esto automáticamente al crear el ticket
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_termino = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.usuario.username} ({self.estado})"

# 2. Tabla Secundaria: El chat del ticket
class MensajeTicket(models.Model):
    ticket = models.ForeignKey(TicketSoporte, on_delete=models.CASCADE, related_name='mensajes')
    
    # Puede ser el jugador pidiendo ayuda o el Admin respondiendo
    remitente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mensajes_enviados')
    
    contenido_mensaje = models.TextField()
    url_adjunto = models.URLField(blank=True, null=True, help_text="Captura extra del usuario")
    
    # Django registrará el momento exacto del mensaje
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.remitente.username} en Ticket #{self.ticket.id}"