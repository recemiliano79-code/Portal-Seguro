from django.contrib import admin
from .models import Tip, TipoAcoso, Institucion, Reporte

# Configuración del Admin para Reportes
@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    # AQUÍ ESTABA EL ERROR: Cambiamos 'estado' por 'status'
    list_display = ('id', 'user', 'tipo_acoso', 'status', 'creado_en')
    
    # TAMBIÉN AQUÍ: Cambiamos 'estado' por 'status'
    list_filter = ('status', 'tipo_acoso', 'creado_en')
    
    search_fields = ('descripcion', 'user__username', 'nombre_reportante')
    date_hierarchy = 'creado_en'

# Configuración para los otros modelos
@admin.register(TipoAcoso)
class TipoAcosoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Institucion)
class InstitucionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'sitio_web')

@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'publicado', 'creado_en')
    list_filter = ('publicado',)