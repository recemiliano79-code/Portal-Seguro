# ── Agrega esto a projects/models.py ──────────────────────────────────────────

from django.db import models
from django.contrib.auth.models import User

class Sugerencia(models.Model):
    TIPO_CHOICES = [
        ('tip',         'Tip de Seguridad'),
        ('institucion', 'Institución'),
        ('tipo_acoso',  'Tipo de Acoso / Glosario'),
        ('otro',        'Otro'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada',  'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    usuario     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sugerencias')
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo      = models.CharField(max_length=200)
    contenido   = models.TextField()
    estado      = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    nota_admin  = models.TextField(blank=True, help_text='Nota del administrador al revisar')
    creado_en   = models.DateTimeField(auto_now_add=True)
    revisado_en = models.DateTimeField(null=True, blank=True)
    revisado_por= models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sugerencias_revisadas')

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Sugerencia'
        verbose_name_plural = 'Sugerencias'

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} — {self.usuario.username}"