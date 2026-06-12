from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from projects.pwa_views import service_worker, manifest, offline

urlpatterns = [
    path('service-worker.js', service_worker, name='service-worker'),
    path('manifest.json',     manifest,       name='manifest'),
    path('offline/',          offline,        name='offline'),

    path('admin/', admin.site.urls),

    # ── favicon (silencia el 404) ───────────────────────────────
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),

    # ── Cuentas: tu vista primero (login/register) ──────────────
    path('accounts/', include('accounts.urls')),

    # ── Django auth: logout + recuperar contraseña ──────────────
    # Solo se usan: logout/, password_reset/, password_reset/done/,
    # reset/<uidb64>/<token>/, reset/done/
    # El login/ de Django queda opacado por el de arriba ✓
    path('accounts/', include('django.contrib.auth.urls')),

    # ── Sentinel AI ─────────────────────────────────────────────
    path('ai/', include('projects.ai_urls')),

    # ── App principal ────────────────────────────────────────────
    path('', include('projects.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)