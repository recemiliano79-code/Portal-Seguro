# ── Agrega estas rutas a projects/urls.py ─────────────────────────────────────

from projects.views import (
    SugerenciaCreateView,
    SugerenciaEnviadaView,
    SugerenciasAdminView,
    SugerenciaRevisarView,
)

# Dentro de urlpatterns añade:
urlpatterns_extra = [
    path('sugerencias/nueva/',           SugerenciaCreateView.as_view(),  name='sugerencia-create'),
    path('sugerencias/enviada/',         SugerenciaEnviadaView.as_view(), name='sugerencia-enviada'),
    path('sugerencias/admin/',           SugerenciasAdminView.as_view(),  name='sugerencias-admin'),
    path('sugerencias/<int:pk>/revisar/',SugerenciaRevisarView.as_view(), name='sugerencia-revisar'),
]