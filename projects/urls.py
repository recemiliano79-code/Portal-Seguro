from django.urls import path
from .views import (
    DashboardView,
    ReporteCreateView, ReporteListView, ReporteDetailView,
    ReporteStatsApiView, AlertasCriticasApiView, NotificacionesUsuarioApiView,
    TipListView, TipCreateView, TipUpdateView, TipDeleteView,
    InstitucionListView, InstitucionCreateView, InstitucionUpdateView, InstitucionDeleteView,
    TipoListView, TipoCreateView, TipoUpdateView, TipoDeleteView,
    SugerenciaCreateView, SugerenciaEnviadaView, SugerenciasAdminView, SugerenciaRevisarView,
)

app_name = 'projects'

urlpatterns = [
    # ── Dashboard ──────────────────────────────────────────────────
    path('', DashboardView.as_view(), name='home'),

    # ── Reportes ───────────────────────────────────────────────────
    path('nuevo-reporte/',         ReporteCreateView.as_view(), name='reporte-create'),
    path('mis-reportes/',          ReporteListView.as_view(),   name='reporte-list'),
    path('reportes/<int:pk>/',     ReporteDetailView.as_view(), name='reporte-detail'),

    # ── APIs (polling tiempo real) ─────────────────────────────────
    path('reportes/api/stats/',          ReporteStatsApiView.as_view(),         name='reporte-stats-api'),
    path('reportes/api/alertas/',        AlertasCriticasApiView.as_view(),      name='alertas-criticas-api'),
    path('reportes/api/notificaciones/', NotificacionesUsuarioApiView.as_view(), name='notificaciones-api'),

    # ── Tips ───────────────────────────────────────────────────────
    path('tips/',                   TipListView.as_view(),   name='tip-list'),
    path('tips/nuevo/',             TipCreateView.as_view(), name='tip-create'),
    path('tips/<int:pk>/editar/',   TipUpdateView.as_view(), name='tip-update'),
    path('tips/<int:pk>/eliminar/', TipDeleteView.as_view(), name='tip-delete'),

    # ── Instituciones ──────────────────────────────────────────────
    path('instituciones/',                   InstitucionListView.as_view(),   name='institucion-list'),
    path('instituciones/nueva/',             InstitucionCreateView.as_view(), name='institucion-create'),
    path('instituciones/<int:pk>/editar/',   InstitucionUpdateView.as_view(), name='institucion-update'),
    path('instituciones/<int:pk>/eliminar/', InstitucionDeleteView.as_view(), name='institucion-delete'),

    # ── Glosario ───────────────────────────────────────────────────
    path('glosario/',                   TipoListView.as_view(),   name='tipo-list'),
    path('glosario/nuevo/',             TipoCreateView.as_view(), name='tipo-create'),
    path('glosario/<int:pk>/editar/',   TipoUpdateView.as_view(), name='tipo-update'),
    path('glosario/<int:pk>/eliminar/', TipoDeleteView.as_view(), name='tipo-delete'),

    # ── Sugerencias ────────────────────────────────────────────────
    path('sugerencias/nueva/',            SugerenciaCreateView.as_view(),  name='sugerencia-create'),
    path('sugerencias/enviada/',          SugerenciaEnviadaView.as_view(), name='sugerencia-enviada'),
    path('sugerencias/admin/',            SugerenciasAdminView.as_view(),  name='sugerencias-admin'),
    path('sugerencias/<int:pk>/revisar/', SugerenciaRevisarView.as_view(), name='sugerencia-revisar'),
]