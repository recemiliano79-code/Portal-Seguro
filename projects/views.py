# ══════════════════════════════════════════════════════════════════
#  projects/views.py  — VERSIÓN COMPLETA v6
#  Cambios:
#   • AlertasCriticasApiView: solo reportes críticos NO revisados
#   • SugerenciaRevisarView: al aprobar, crea automáticamente
#     Tip / Institución / TipoAcoso según el tipo de sugerencia
#   • ReporteCreateView: acepta foto_evidencia (enctype multipart)
#   • ReporteDetailView: muestra foto solo al admin
# ══════════════════════════════════════════════════════════════════

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Case, When, IntegerField
from .models import Tip, TipoAcoso, Institucion, Reporte, Sugerencia, MensajeAdmin
from .forms import TipForm, TipoAcosoForm, InstitucionForm, ReporteForm


def _is_admin(user):
    return user.is_staff or user.username == 'recemilian79'


URGENCIA_ORDER = Case(
    When(nivel_urgencia='critico', then=0),
    When(nivel_urgencia='alto',    then=1),
    When(nivel_urgencia='medio',   then=2),
    When(nivel_urgencia='bajo',    then=3),
    default=4,
    output_field=IntegerField()
)


class SidebarMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_admin']           = _is_admin(self.request.user)
        ctx['mis_reportes_count'] = Reporte.objects.filter(user=self.request.user).count()
        ctx['pendientes_global']  = Sugerencia.objects.filter(estado='pendiente').count()
        ctx['mensajes_no_leidos'] = MensajeAdmin.objects.filter(
            reporte__user=self.request.user, leido=False, es_del_admin=True
        ).count()
        if _is_admin(self.request.user):
            # ── Solo críticos SIN revisar ──────────────────────────
            ctx['alertas_criticas'] = Reporte.objects.filter(
                nivel_urgencia='critico', revisado=False
            ).select_related('user').order_by('-creado_en')[:5]
            ctx['total_alertas_criticas'] = Reporte.objects.filter(
                nivel_urgencia='critico', revisado=False
            ).count()
        return ctx


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return _is_admin(self.request.user)


# ══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        is_admin = _is_admin(request.user)
        base_ctx = {
            'is_admin':           is_admin,
            'mis_reportes_count': Reporte.objects.filter(user=request.user).count(),
            'pendientes_global':  Sugerencia.objects.filter(estado='pendiente').count(),
            'mensajes_no_leidos': MensajeAdmin.objects.filter(
                reporte__user=request.user, leido=False, es_del_admin=True
            ).count(),
            'no_back': True,
        }

        if is_admin:
            from datetime import timedelta, date
            today = date.today()
            grafica_labels, grafica_data = [], []
            for i in range(6, -1, -1):
                day   = today - timedelta(days=i)
                count = Reporte.objects.filter(creado_en__date=day).count()
                grafica_labels.append(day.strftime('%d/%m'))
                grafica_data.append(count)

            dona_data = {
                'critico': Reporte.objects.filter(nivel_urgencia='critico').count(),
                'alto':    Reporte.objects.filter(nivel_urgencia='alto').count(),
                'medio':   Reporte.objects.filter(nivel_urgencia='medio').count(),
                'bajo':    Reporte.objects.filter(nivel_urgencia='bajo').count(),
            }
            # Solo críticos sin revisar para alertas
            alertas_criticas = Reporte.objects.filter(
                nivel_urgencia='critico', revisado=False
            ).select_related('user').order_by('-creado_en')[:5]

            ctx = {
                **base_ctx,
                'total_reportes':         Reporte.objects.count(),
                'reportes_urgentes':      Reporte.objects.filter(nivel_urgencia='critico').count(),
                'reportes_nuevos':        Reporte.objects.filter(revisado=False).count(),
                'total_usuarios':         User.objects.count(),
                'sugerencias_pend':       Sugerencia.objects.filter(estado='pendiente').count(),
                'reportes_recientes':     Reporte.objects.select_related('user').annotate(
                    urgencia_order=URGENCIA_ORDER).order_by('urgencia_order', '-creado_en')[:8],
                'usuarios_recientes':     User.objects.order_by('-date_joined')[:6],
                'reportes_urgentes_list': alertas_criticas,
                'all_reportes':           Reporte.objects.select_related('user').annotate(
                    urgencia_order=URGENCIA_ORDER).order_by('urgencia_order', '-creado_en')[:20],
                'grafica_labels':         grafica_labels,
                'grafica_data':           grafica_data,
                'dona_data':              dona_data,
                'alertas_criticas':       alertas_criticas,
                'total_alertas_criticas': alertas_criticas.count(),
            }
            return render(request, 'projects/dashboard_admin.html', ctx)

        else:
            mis_reportes = Reporte.objects.filter(
                user=request.user
            ).annotate(urgencia_order=URGENCIA_ORDER).order_by('urgencia_order', '-creado_en')

            MensajeAdmin.objects.filter(
                reporte__user=request.user, leido=False, es_del_admin=True
            ).update(leido=True)

            notificaciones = []
            for rep in mis_reportes:
                if rep.status == 'revision':
                    notificaciones.append({'tipo': 'revision', 'icon': '⏳',
                        'texto': f'Tu reporte #{rep.pk} está siendo revisado.',
                        'sub':   'El equipo revisará los detalles y te contactará pronto.',
                        'reporte': rep})
                elif rep.status == 'proceso':
                    notificaciones.append({'tipo': 'proceso', 'icon': '⚙️',
                        'texto': f'Tu reporte #{rep.pk} está en proceso de atención.',
                        'sub':   'Se están tomando acciones para atender tu caso.',
                        'reporte': rep})
                elif rep.status == 'cerrado':
                    notificaciones.append({'tipo': 'cerrado', 'icon': '✅',
                        'texto': f'Tu reporte #{rep.pk} ha sido cerrado.',
                        'sub':   'Si necesitas reabrir el caso, contacta al equipo.',
                        'reporte': rep})
                msgs_count = MensajeAdmin.objects.filter(reporte=rep, es_del_admin=True).count()
                if msgs_count:
                    notificaciones.append({'tipo': 'mensaje', 'icon': '💬',
                        'texto': f'El equipo te dejó un mensaje en el reporte #{rep.pk}.',
                        'sub':   f'{msgs_count} mensaje{"s" if msgs_count > 1 else ""} del equipo Sentinel.',
                        'reporte': rep})

            ctx = {
                **base_ctx,
                'mis_reportes':    mis_reportes[:5],
                'tips_destacados': Tip.objects.filter(publicado=True)[:3],
                'instituciones':   Institucion.objects.all()[:4],
                'notificaciones':  notificaciones[:5],
            }
            return render(request, 'projects/dashboard_user.html', ctx)


# ══════════════════════════════════════════════════════════════════
#  APIs
# ══════════════════════════════════════════════════════════════════

class ReporteStatsApiView(LoginRequiredMixin, View):
    def get(self, request):
        if not _is_admin(request.user):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        from datetime import timedelta, date
        today = date.today()
        labels, data = [], []
        for i in range(6, -1, -1):
            day   = today - timedelta(days=i)
            count = Reporte.objects.filter(creado_en__date=day).count()
            labels.append(day.strftime('%d/%m'))
            data.append(count)
        dona = {
            'critico': Reporte.objects.filter(nivel_urgencia='critico').count(),
            'alto':    Reporte.objects.filter(nivel_urgencia='alto').count(),
            'medio':   Reporte.objects.filter(nivel_urgencia='medio').count(),
            'bajo':    Reporte.objects.filter(nivel_urgencia='bajo').count(),
        }
        totales = {
            'total':       Reporte.objects.count(),
            'criticos':    dona['critico'],
            'sin_revisar': Reporte.objects.filter(revisado=False).count(),
            'usuarios':    User.objects.count(),
        }
        # Solo críticos sin revisar para el polling de alertas
        alertas = list(
            Reporte.objects.filter(nivel_urgencia='critico', revisado=False)
            .values('pk', 'nombre_reportante', 'creado_en', 'descripcion', 'lugar')
            .order_by('-creado_en')[:5]
        )
        for a in alertas:
            a['creado_en'] = a['creado_en'].strftime('%d/%m/%Y %H:%M')
        return JsonResponse({'labels': labels, 'data': data, 'dona': dona,
                             'totales': totales, 'alertas': alertas})


class AlertasCriticasApiView(LoginRequiredMixin, View):
    """
    Polling cada 30s.
    Solo devuelve reportes críticos con revisado=False.
    En cuanto el admin marca como revisado, desaparecen de las alertas.
    """
    def get(self, request):
        if not _is_admin(request.user):
            return JsonResponse({'error': 'Sin permisos'}, status=403)

        # ← CLAVE: revisado=False para que desaparezcan al marcar revisado
        qs = Reporte.objects.filter(
            nivel_urgencia='critico', revisado=False
        ).order_by('-creado_en')[:10]

        alertas = [{
            'pk':          r.pk,
            'nombre':      r.nombre_reportante or 'Anónimo',
            'descripcion': (r.descripcion or '')[:80],
            'lugar':       r.lugar or '—',
            'llamar_911':  r.llamar_911,
            'creado_en':   r.creado_en.strftime('%d/%m/%Y %H:%M'),
            'url':         f'/reportes/{r.pk}/',
        } for r in qs]

        return JsonResponse({'total': len(alertas), 'alertas': alertas})


class NotificacionesUsuarioApiView(LoginRequiredMixin, View):
    def get(self, request):
        mis_reportes = Reporte.objects.filter(
            user=request.user
        ).annotate(urgencia_order=URGENCIA_ORDER).order_by('urgencia_order', '-creado_en')

        notifs = []
        for rep in mis_reportes:
            if rep.status in ('revision', 'proceso', 'cerrado'):
                lmap = {
                    'revision': ('⏳', 'En Revisión',  f'Tu reporte #{rep.pk} está siendo revisado.'),
                    'proceso':  ('⚙️', 'En Proceso',   f'Tu reporte #{rep.pk} está en proceso.'),
                    'cerrado':  ('✅', 'Cerrado',       f'Tu reporte #{rep.pk} ha sido cerrado.'),
                }
                icon, label, txt = lmap[rep.status]
                notifs.append({'tipo': rep.status, 'icon': icon, 'label': label, 'texto': txt, 'pk': rep.pk})
            msgs_count = MensajeAdmin.objects.filter(reporte=rep, es_del_admin=True, leido=False).count()
            if msgs_count:
                notifs.append({
                    'tipo': 'mensaje', 'icon': '💬', 'label': 'Nuevo mensaje',
                    'texto': f'El equipo te dejó {msgs_count} mensaje(s) en el reporte #{rep.pk}.',
                    'pk': rep.pk,
                })
        return JsonResponse({'total': len(notifs), 'notificaciones': notifs})


# ══════════════════════════════════════════════════════════════════
#  REPORTES
# ══════════════════════════════════════════════════════════════════

class ReporteCreateView(SidebarMixin, LoginRequiredMixin, CreateView):
    model         = Reporte
    form_class    = ReporteForm
    template_name = 'projects/reporte_form.html'
    success_url   = reverse_lazy('projects:reporte-list')

    def get_initial(self):
        initial = super().get_initial()
        user    = self.request.user
        ultimo  = Reporte.objects.filter(user=user).order_by('-creado_en').first()
        if ultimo:
            if ultimo.nombre_reportante:   initial['nombre_reportante']   = ultimo.nombre_reportante
            if ultimo.correo_reportante:   initial['correo_reportante']   = ultimo.correo_reportante
            if ultimo.telefono_reportante: initial['telefono_reportante'] = ultimo.telefono_reportante
        else:
            if user.first_name or user.last_name:
                initial['nombre_reportante'] = f'{user.first_name} {user.last_name}'.strip()
            if user.email:
                initial['correo_reportante'] = user.email
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos_acoso']    = TipoAcoso.objects.all()
        ctx['instituciones']  = Institucion.objects.all()
        ctx['no_back']        = True
        ctx['ultimo_reporte'] = Reporte.objects.filter(user=self.request.user).order_by('-creado_en').first()
        return ctx

    def post(self, request, *args, **kwargs):
        # Necesario para que Django procese request.FILES (foto)
        self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs['files'] = self.request.FILES
        return kwargs

    def form_valid(self, form):
        form.instance.user   = self.request.user
        form.instance.status = form.instance.status or 'nuevo'
        resp  = super().form_valid(form)
        nivel = form.instance.nivel_urgencia

        msg_map = {
            'critico': (messages.error,   '🚨 Reporte CRÍTICO enviado. El equipo lo atenderá con prioridad máxima. Si tu seguridad está en riesgo inmediato, llama al 911.'),
            'alto':    (messages.warning, '⚠️ Reporte ALTO enviado. Nos pondremos en contacto contigo pronto.'),
            'medio':   (messages.info,    '⚡ Reporte MEDIO enviado. Lo atenderemos en breve.'),
            'bajo':    (messages.success, '✅ Reporte enviado correctamente. El equipo lo revisará.'),
        }
        fn, txt = msg_map.get(nivel, (messages.success, '✅ Reporte enviado.'))
        fn(self.request, txt)

        if form.instance.llamar_911:
            MensajeAdmin.objects.create(
                reporte=form.instance,
                autor=self.request.user,
                texto='🚨 ALERTA: La reportante solicitó contacto urgente con autoridades (llamar al 911).',
                es_del_admin=False,
            )
        return resp


class ReporteListView(SidebarMixin, LoginRequiredMixin, ListView):
    model               = Reporte
    template_name       = 'projects/reporte_list.html'
    context_object_name = 'reportes'

    def get_queryset(self):
        if _is_admin(self.request.user):
            qs     = Reporte.objects.select_related('user').annotate(urgencia_order=URGENCIA_ORDER)
            nivel  = self.request.GET.get('nivel', '')
            estado = self.request.GET.get('revisado', '')
            if nivel:         qs = qs.filter(nivel_urgencia=nivel)
            if estado == '0': qs = qs.filter(revisado=False)
            if estado == '1': qs = qs.filter(revisado=True)
            return qs.order_by('urgencia_order', '-creado_en')
        return Reporte.objects.filter(
            user=self.request.user
        ).annotate(urgencia_order=URGENCIA_ORDER).order_by('urgencia_order', '-creado_en')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user_qs = Reporte.objects.filter(user=self.request.user).annotate(urgencia_order=URGENCIA_ORDER)
        ctx['activos']   = user_qs.exclude(status='cerrado').count()
        ctx['cerrados']  = user_qs.filter(status='cerrado').count()
        ultimo           = user_qs.order_by('urgencia_order').first()
        ctx['nivel_max'] = ultimo.nivel_urgencia if ultimo else None
        if _is_admin(self.request.user):
            ctx['criticos']        = Reporte.objects.filter(nivel_urgencia='critico').count()
            ctx['altos']           = Reporte.objects.filter(nivel_urgencia='alto').count()
            ctx['sin_revisar']     = Reporte.objects.filter(revisado=False).count()
            ctx['nivel_actual']    = self.request.GET.get('nivel', '')
            ctx['revisado_actual'] = self.request.GET.get('revisado', '')
        return ctx


class ReporteDetailView(SidebarMixin, LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)
        if not _is_admin(request.user) and reporte.user != request.user:
            messages.error(request, 'Sin permisos.')
            return redirect('projects:reporte-list')
        MensajeAdmin.objects.filter(reporte=reporte, leido=False, es_del_admin=True).update(leido=True)
        is_admin     = _is_admin(request.user)
        notif_estado = None
        if not is_admin and reporte.status != 'nuevo':
            estados = {
                'revision': ('info',    '⏳ Tu reporte está siendo revisado por el equipo Sentinel.'),
                'proceso':  ('warning', '⚙️ Tu reporte está en proceso de atención activa.'),
                'cerrado':  ('success', '✅ Tu reporte ha sido cerrado por el equipo.'),
            }
            notif_estado = estados.get(reporte.status)
        ctx = {
            'reporte':            reporte,
            'mensajes':           reporte.mensajes.all(),
            'is_admin':           is_admin,
            'mis_reportes_count': Reporte.objects.filter(user=request.user).count(),
            'pendientes_global':  Sugerencia.objects.filter(estado='pendiente').count(),
            'mensajes_no_leidos': MensajeAdmin.objects.filter(
                reporte__user=request.user, leido=False, es_del_admin=True).count(),
            'notif_estado': notif_estado,
            'no_back':      False,
        }
        return render(request, 'projects/reporte_detail.html', ctx)

    def post(self, request, pk):
        reporte  = get_object_or_404(Reporte, pk=pk)
        if not _is_admin(request.user) and reporte.user != request.user:
            return redirect('projects:reporte-list')

        is_admin = _is_admin(request.user)
        texto    = request.POST.get('texto', '').strip()

        if is_admin:
            cambio_realizado = False
            nuevo_status = request.POST.get('nuevo_status', '')
            if nuevo_status in dict(Reporte.STATUS_CHOICES) and nuevo_status != reporte.status:
                reporte.status   = nuevo_status
                cambio_realizado = True

            if request.POST.get('marcar_revisado') and not reporte.revisado:
                reporte.revisado     = True
                reporte.revisado_por = request.user
                reporte.revisado_en  = timezone.now()
                cambio_realizado     = True

            if cambio_realizado:
                reporte.save()
                labels = {
                    'revision': 'ha pasado a revisión',
                    'proceso':  'está en proceso de atención',
                    'cerrado':  'ha sido cerrado',
                    'nuevo':    'ha sido reabierto',
                }
                if nuevo_status in labels and reporte.user:
                    MensajeAdmin.objects.create(
                        reporte=reporte, autor=request.user,
                        texto=f'📢 Tu reporte #{reporte.pk} {labels[nuevo_status]}. Puedes ver los detalles en esta página.',
                        es_del_admin=True, leido=False,
                    )
                messages.success(request, f'✅ Estado actualizado a "{reporte.get_status_display()}".')

            if texto:
                MensajeAdmin.objects.create(
                    reporte=reporte, autor=request.user,
                    texto=texto, es_del_admin=True,
                )
                if not cambio_realizado:
                    messages.success(request, 'Mensaje enviado.')
        else:
            if texto:
                MensajeAdmin.objects.create(
                    reporte=reporte, autor=request.user,
                    texto=texto, es_del_admin=False,
                )
                messages.success(request, 'Mensaje enviado al equipo Sentinel.')

        return redirect('projects:reporte-detail', pk=pk)


# ══════════════════════════════════════════════════════════════════
#  GLOSARIO / INSTITUCIONES / TIPS
# ══════════════════════════════════════════════════════════════════

class TipoListView(SidebarMixin, LoginRequiredMixin, ListView):
    model=TipoAcoso; template_name='projects/tipo_list.html'

class TipoCreateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model=TipoAcoso; form_class=TipoAcosoForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:tipo-list'); extra_context={'title':'Nuevo Tipo de Acoso'}

class TipoUpdateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    model=TipoAcoso; form_class=TipoAcosoForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:tipo-list'); extra_context={'title':'Editar Tipo de Acoso'}

class TipoDeleteView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    model=TipoAcoso; template_name='projects/confirm_delete.html'
    success_url=reverse_lazy('projects:tipo-list')


class InstitucionListView(SidebarMixin, LoginRequiredMixin, ListView):
    model=Institucion; template_name='projects/institucion_list.html'

class InstitucionCreateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model=Institucion; form_class=InstitucionForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:institucion-list'); extra_context={'title':'Nueva Institución Aliada'}

class InstitucionUpdateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    model=Institucion; form_class=InstitucionForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:institucion-list'); extra_context={'title':'Editar Institución'}

class InstitucionDeleteView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    model=Institucion; template_name='projects/confirm_delete.html'
    success_url=reverse_lazy('projects:institucion-list')


class TipListView(SidebarMixin, LoginRequiredMixin, ListView):
    model=Tip; template_name='projects/tip_list.html'
    def get_queryset(self):
        # Admin ve todos; usuarios solo los publicados
        if _is_admin(self.request.user):
            return Tip.objects.all()
        return Tip.objects.filter(publicado=True)

class TipCreateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, CreateView):
    model=Tip; form_class=TipForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:tip-list'); extra_context={'title':'Nuevo Consejo de Seguridad'}

class TipUpdateView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, UpdateView):
    model=Tip; form_class=TipForm; template_name='projects/form_generic.html'
    success_url=reverse_lazy('projects:tip-list'); extra_context={'title':'Editar Consejo'}

class TipDeleteView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, DeleteView):
    model=Tip; template_name='projects/confirm_delete.html'
    success_url=reverse_lazy('projects:tip-list')


# ══════════════════════════════════════════════════════════════════
#  SUGERENCIAS
# ══════════════════════════════════════════════════════════════════

class SugerenciaCreateView(SidebarMixin, LoginRequiredMixin, CreateView):
    model=Sugerencia; fields=['tipo','titulo','contenido']
    template_name='projects/sugerencia_form.html'
    success_url=reverse_lazy('projects:sugerencia-enviada')
    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, '¡Sugerencia enviada!')
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipo_inicial'] = self.request.GET.get('tipo', '')
        return ctx

class SugerenciaEnviadaView(SidebarMixin, LoginRequiredMixin, TemplateView):
    template_name = 'projects/sugerencia_enviada.html'

class SugerenciasAdminView(SidebarMixin, AdminRequiredMixin, LoginRequiredMixin, ListView):
    model=Sugerencia; template_name='projects/sugerencias_admin.html'
    context_object_name='sugerencias'
    def get_queryset(self):
        qs     = Sugerencia.objects.select_related('usuario','revisado_por').all()
        estado = self.request.GET.get('estado','')
        tipo   = self.request.GET.get('tipo','')
        if estado: qs=qs.filter(estado=estado)
        if tipo:   qs=qs.filter(tipo=tipo)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pendientes']    = Sugerencia.objects.filter(estado='pendiente').count()
        ctx['aprobadas']     = Sugerencia.objects.filter(estado='aprobada').count()
        ctx['rechazadas']    = Sugerencia.objects.filter(estado='rechazada').count()
        ctx['estado_actual'] = self.request.GET.get('estado','')
        ctx['tipo_actual']   = self.request.GET.get('tipo','')
        return ctx


class SugerenciaRevisarView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not _is_admin(request.user):
            return redirect('projects:sugerencias-admin')

        sug    = get_object_or_404(Sugerencia, pk=pk)
        accion = request.POST.get('accion')

        if accion == 'aprobar':
            sug.estado = 'aprobada'

            # ── AUTO-PUBLICACIÓN según el tipo de sugerencia ──────
            creado = None
            if sug.tipo == 'tip':
                creado = Tip.objects.create(
                    titulo    = sug.titulo,
                    contenido = sug.contenido,
                    publicado = True,          # ← publicado automáticamente
                )
                messages.success(request,
                    f'✅ Sugerencia aprobada. Tip "{creado.titulo}" publicado automáticamente.')

            elif sug.tipo == 'institucion':
                creado = Institucion.objects.create(
                    nombre = sug.titulo,
                    notas  = sug.contenido,
                )
                messages.success(request,
                    f'✅ Sugerencia aprobada. Institución "{creado.nombre}" añadida automáticamente.')

            elif sug.tipo == 'tipo_acoso':
                creado = TipoAcoso.objects.create(
                    nombre      = sug.titulo,
                    descripcion = sug.contenido,
                )
                messages.success(request,
                    f'✅ Sugerencia aprobada. Definición "{creado.nombre}" añadida al glosario.')

            else:
                # tipo='otro' — no crea registro, solo aprueba
                messages.success(request, '✅ Sugerencia aprobada.')

        elif accion == 'rechazar':
            sug.estado = 'rechazada'
            messages.warning(request, '⚠️ Sugerencia rechazada.')

        sug.nota_admin   = request.POST.get('nota_admin', '')
        sug.revisado_en  = timezone.now()
        sug.revisado_por = request.user
        sug.save()
        return redirect('projects:sugerencias-admin')