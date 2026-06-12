# ── Agrega esto a projects/views.py ───────────────────────────────────────────

from django.views.generic import CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Sugerencia

# ── Mixin: solo admin ─────────────────────────────────────────────────────────
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or \
               self.request.user.username == 'recemilian79'


# ── Vista: enviar sugerencia (cualquier usuario logueado) ─────────────────────
class SugerenciaCreateView(LoginRequiredMixin, CreateView):
    model         = Sugerencia
    fields        = ['tipo', 'titulo', 'contenido']
    template_name = 'projects/sugerencia_form.html'
    success_url   = reverse_lazy('projects:sugerencia-enviada')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, '¡Sugerencia enviada! El administrador la revisará pronto.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_admin']          = self.request.user.is_staff or self.request.user.username == 'recemilian79'
        ctx['mis_reportes_count']= __import__('projects.models', fromlist=['Reporte']).Reporte.objects.filter(user=self.request.user).count()
        ctx['tipo_inicial']      = self.request.GET.get('tipo', '')
        return ctx


# ── Vista: confirmación enviada ───────────────────────────────────────────────
from django.views.generic import TemplateView
class SugerenciaEnviadaView(LoginRequiredMixin, TemplateView):
    template_name = 'projects/sugerencia_enviada.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_admin']          = self.request.user.is_staff or self.request.user.username == 'recemilian79'
        ctx['mis_reportes_count']= __import__('projects.models', fromlist=['Reporte']).Reporte.objects.filter(user=self.request.user).count()
        return ctx


# ── Vista: panel admin de sugerencias ────────────────────────────────────────
class SugerenciasAdminView(AdminRequiredMixin, LoginRequiredMixin, ListView):
    model         = Sugerencia
    template_name = 'projects/sugerencias_admin.html'
    context_object_name = 'sugerencias'

    def get_queryset(self):
        qs = Sugerencia.objects.select_related('usuario', 'revisado_por').all()
        estado = self.request.GET.get('estado', '')
        tipo   = self.request.GET.get('tipo', '')
        if estado: qs = qs.filter(estado=estado)
        if tipo:   qs = qs.filter(tipo=tipo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_admin']          = True
        ctx['mis_reportes_count']= __import__('projects.models', fromlist=['Reporte']).Reporte.objects.filter(user=self.request.user).count()
        ctx['pendientes']        = Sugerencia.objects.filter(estado='pendiente').count()
        ctx['aprobadas']         = Sugerencia.objects.filter(estado='aprobada').count()
        ctx['rechazadas']        = Sugerencia.objects.filter(estado='rechazada').count()
        ctx['estado_actual']     = self.request.GET.get('estado', '')
        ctx['tipo_actual']       = self.request.GET.get('tipo', '')
        return ctx


# ── Acción: aprobar / rechazar sugerencia (admin) ─────────────────────────────
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class SugerenciaRevisarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not (request.user.is_staff or request.user.username == 'recemilian79'):
            messages.error(request, 'Sin permisos.')
            return redirect('projects:sugerencias-admin')
        sug    = get_object_or_404(Sugerencia, pk=pk)
        accion = request.POST.get('accion')  # 'aprobar' o 'rechazar'
        nota   = request.POST.get('nota_admin', '')
        if accion == 'aprobar':
            sug.estado = 'aprobada'
            messages.success(request, f'Sugerencia "{sug.titulo}" aprobada.')
        elif accion == 'rechazar':
            sug.estado = 'rechazada'
            messages.warning(request, f'Sugerencia "{sug.titulo}" rechazada.')
        sug.nota_admin   = nota
        sug.revisado_en  = timezone.now()
        sug.revisado_por = request.user
        sug.save()
        return redirect('projects:sugerencias-admin')