from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


# ==========================================
# 1. GLOSARIO (Tipos de Acoso)
# ==========================================
class TipoAcoso(models.Model):
    nombre      = models.CharField(max_length=100, verbose_name="Nombre del tipo")
    descripcion = models.TextField(blank=True, verbose_name="Descripción o Definición")

    class Meta:
        verbose_name        = 'Tipo de Acoso'
        verbose_name_plural = 'Glosario de Acosos'

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('projects:tipo-list')


# ==========================================
# 2. INSTITUCIONES ALIADAS
# ==========================================
class Institucion(models.Model):
    nombre    = models.CharField(max_length=200, verbose_name="Nombre de la Institución")
    direccion = models.CharField(max_length=250, blank=True)
    telefono  = models.CharField(max_length=50,  blank=True)
    email     = models.EmailField(blank=True)
    sitio_web = models.URLField(blank=True)
    notas     = models.TextField(blank=True, verbose_name="Notas adicionales")

    class Meta:
        verbose_name        = 'Institución'
        verbose_name_plural = 'Instituciones'

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('projects:institucion-list')


# ==========================================
# 3. TIPS (CONSEJOS)
# ==========================================
class Tip(models.Model):
    titulo         = models.CharField(max_length=200)
    contenido      = models.TextField()
    publicado      = models.BooleanField(default=True)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Consejo'
        verbose_name_plural = 'Consejos de Seguridad'
        ordering            = ['-creado_en']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('projects:tip-list')


# ==========================================
# 4. REPORTES
# ==========================================
class Reporte(models.Model):
    STATUS_CHOICES = [
        ('nuevo',    'Nuevo'),
        ('revision', 'En Revisión'),
        ('proceso',  'En Proceso'),
        ('cerrado',  'Cerrado'),
    ]
    URGENCIA_CHOICES = [
        ('critico', 'Crítico'),
        ('alto',    'Alto'),
        ('medio',   'Medio'),
        ('bajo',    'Bajo / Informativo'),
    ]

    # ── Usuario ───────────────────────────────────────────────────
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="Usuario del Sistema"
    )

    # ── Datos del reportante ──────────────────────────────────────
    nombre_reportante   = models.CharField(max_length=200, verbose_name="Nombre Completo", blank=True, null=True)
    correo_reportante   = models.EmailField(verbose_name="Correo",    blank=True, null=True)
    telefono_reportante = models.CharField(max_length=50,  verbose_name="Teléfono", blank=True, null=True)

    # ── Detalle del incidente ─────────────────────────────────────
    descripcion  = models.TextField(verbose_name="Descripción de los hechos")
    fecha_suceso = models.DateField(null=True, blank=True)
    lugar        = models.CharField(max_length=250, blank=True, verbose_name="Lugar de los hechos")

    # ── NUEVO: Foto de evidencia ──────────────────────────────────
    foto_evidencia = models.ImageField(
        upload_to='reportes/fotos/',
        null=True, blank=True,
        verbose_name="Foto de evidencia (opcional)"
    )

    # ── Relaciones ────────────────────────────────────────────────
    tipo_acoso  = models.ForeignKey(TipoAcoso,  on_delete=models.SET_NULL, null=True, blank=True)
    institucion = models.ForeignKey(Institucion, on_delete=models.SET_NULL, null=True, blank=True)

    # ── Estado del reporte ────────────────────────────────────────
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='nuevo', verbose_name="Estado"
    )

    # ── Urgencia ──────────────────────────────────────────────────
    nivel_urgencia = models.CharField(
        max_length=10, choices=URGENCIA_CHOICES,
        default='medio', verbose_name="Nivel de urgencia"
    )
    llamar_911 = models.BooleanField(
        default=False,
        verbose_name="Solicitó contacto urgente"
    )

    # ── Revisión ──────────────────────────────────────────────────
    revisado     = models.BooleanField(default=False, verbose_name="Revisado por admin")
    revisado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reportes_revisados',
        verbose_name="Revisado por"
    )
    revisado_en = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────────────
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering            = ['-creado_en']

    def __str__(self):
        return f"Reporte #{self.pk} - {self.nombre_reportante or 'Anónimo'}"

    def get_absolute_url(self):
        return reverse('projects:reporte-detail', kwargs={'pk': self.pk})


# ==========================================
# 5. SUGERENCIAS
# ==========================================
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

    usuario      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sugerencias')
    tipo         = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo       = models.CharField(max_length=200)
    contenido    = models.TextField()
    estado       = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    nota_admin   = models.TextField(blank=True)
    creado_en    = models.DateTimeField(auto_now_add=True)
    revisado_en  = models.DateTimeField(null=True, blank=True)
    revisado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sugerencias_revisadas'
    )

    class Meta:
        ordering            = ['-creado_en']
        verbose_name        = 'Sugerencia'
        verbose_name_plural = 'Sugerencias'

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} — {self.usuario.username}"


# ==========================================
# 6. MENSAJES ADMIN ↔ USUARIO
# ==========================================
class MensajeAdmin(models.Model):
    reporte      = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name='mensajes')
    autor        = models.ForeignKey(User,    on_delete=models.CASCADE, related_name='mensajes_enviados')
    texto        = models.TextField()
    es_del_admin = models.BooleanField(default=True)
    creado_en    = models.DateTimeField(auto_now_add=True)
    leido        = models.BooleanField(default=False)

    class Meta:
        ordering            = ['creado_en']
        verbose_name        = 'Mensaje del Admin'
        verbose_name_plural = 'Mensajes Admin'

    def __str__(self):
        return f"Msg #{self.pk} en Reporte #{self.reporte.pk}"