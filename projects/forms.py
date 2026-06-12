from django import forms
from .models import Tip, TipoAcoso, Institucion, Reporte


class BaseStyleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget   = field.widget
            is_check  = isinstance(widget, forms.CheckboxInput)
            is_select = isinstance(widget, forms.Select)
            is_radio  = isinstance(widget, forms.RadioSelect)
            is_file   = isinstance(widget, forms.ClearableFileInput)

            if is_check:
                widget.attrs.update({'class': 'form-check-input'})
            elif is_radio:
                widget.attrs.update({'class': 'urgencia-radio'})
            elif is_file:
                # File inputs get their own style
                widget.attrs.update({'class': 'form-file-input'})
            else:
                widget.attrs.update({
                    'class': 'form-control',
                    'style': (
                        'background:rgba(255,255,255,.05);'
                        'border:1px solid rgba(255,255,255,.1);'
                        'color:white;padding:12px;border-radius:10px;width:100%;'
                    ),
                })
                if not isinstance(widget, forms.Textarea):
                    widget.attrs['placeholder'] = field.label or field_name

            if is_select:
                field.empty_label = 'Seleccione una opción...'


class TipoAcosoForm(BaseStyleForm):
    class Meta:
        model  = TipoAcoso
        fields = ['nombre', 'descripcion']
        labels = {
            'nombre':      'Nombre del tipo de acoso',
            'descripcion': 'Descripción breve',
        }


class InstitucionForm(BaseStyleForm):
    class Meta:
        model   = Institucion
        fields  = ['nombre', 'direccion', 'telefono', 'email', 'sitio_web', 'notas']
        widgets = {'notas': forms.Textarea(attrs={'rows': 3})}


class TipForm(BaseStyleForm):
    class Meta:
        model   = Tip
        fields  = ['titulo', 'contenido', 'publicado']
        widgets = {'contenido': forms.Textarea(attrs={'rows': 4})}


class ReporteForm(BaseStyleForm):
    nivel_urgencia = forms.ChoiceField(
        choices=Reporte.URGENCIA_CHOICES,
        widget=forms.RadioSelect,
        initial='medio',
        label='Nivel de urgencia',
        help_text='Selecciona el nivel que mejor describe la situación',
    )

    class Meta:
        model  = Reporte
        fields = [
            'nombre_reportante',
            'correo_reportante',
            'telefono_reportante',
            'tipo_acoso',
            'institucion',
            'descripcion',
            'fecha_suceso',
            'lugar',
            'nivel_urgencia',
            'llamar_911',
            'foto_evidencia',      # ← NUEVO
        ]
        labels = {
            'nombre_reportante':   'Nombre completo',
            'correo_reportante':   'Correo electrónico',
            'telefono_reportante': 'Teléfono de contacto',
            'tipo_acoso':          'Tipo de acoso',
            'institucion':         'Institución (opcional)',
            'descripcion':         'Descripción detallada de los hechos',
            'lugar':               'Lugar del suceso',
            'llamar_911':          '¿Necesitas contacto urgente con autoridades?',
            'foto_evidencia':      'Foto de evidencia (opcional)',
        }
        widgets = {
            'fecha_suceso':    forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descripcion':     forms.Textarea(attrs={'rows': 5}),
            'foto_evidencia':  forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }