# projects/pwa_views.py
# Vistas para servir el Service Worker y el offline page desde Django

from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
import json, os

# ── Service Worker ──────────────────────────────────────────
@never_cache
@require_GET
def service_worker(request):
    """
    Sirve el service worker con el Content-Type correcto.
    Debe estar en el root scope (/service-worker.js), no en /static/.
    """
    sw_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'static', 'js', 'service-worker.js'
    )
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        content = "/* Service Worker no encontrado */"

    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# ── Manifest ────────────────────────────────────────────────
@require_GET
def manifest(request):
    """
    Sirve el manifest.json con el Content-Type correcto.
    """
    manifest_data = {
        "name": "Portal Seguro · Sentinel v9",
        "short_name": "Portal Seguro",
        "description": "Portal seguro y confidencial para reportar acoso en CDMX",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#04020f",
        "theme_color": "#7c3aed",
        "orientation": "portrait-primary",
        "lang": "es-MX",
        "scope": "/",
        "icons": [
            {"src": request.build_absolute_uri("/static/icons/icon-72.png"),  "sizes": "72x72",   "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-96.png"),  "sizes": "96x96",   "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-128.png"), "sizes": "128x128", "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-144.png"), "sizes": "144x144", "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-152.png"), "sizes": "152x152", "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-384.png"), "sizes": "384x384", "type": "image/png", "purpose": "any maskable"},
            {"src": request.build_absolute_uri("/static/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
        "shortcuts": [
            {
                "name": "Nuevo Reporte",
                "short_name": "Reportar",
                "url": "/reporte/nuevo/",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}]
            },
            {
                "name": "Sentinel AI",
                "short_name": "AI",
                "url": "/?ai=1",
                "icons": [{"src": "/static/icons/icon-96.png", "sizes": "96x96"}]
            }
        ],
        "categories": ["security", "social", "utilities"]
    }
    return JsonResponse(manifest_data)


# ── Offline fallback page ────────────────────────────────────
@require_GET
def offline(request):
    """
    Página que muestra el SW cuando no hay conexión.
    """
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sin conexión · Portal Seguro</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{
    font-family:system-ui,-apple-system,sans-serif;
    background:#04020f;color:#f0edff;
    display:flex;align-items:center;justify-content:center;
    min-height:100vh;flex-direction:column;gap:20px;
    text-align:center;padding:28px;
  }
  .shield{font-size:4rem;animation:pulse 2s infinite;}
  @keyframes pulse{0%,100%{transform:scale(1);}50%{transform:scale(1.08);}}
  h1{font-size:1.5rem;font-weight:900;letter-spacing:-.5px;}
  p{color:#9488b8;font-size:.9rem;max-width:320px;line-height:1.65;}
  .em{display:flex;flex-direction:column;gap:10px;width:100%;max-width:280px;}
  a{
    display:flex;align-items:center;justify-content:center;gap:8px;
    padding:13px 20px;border-radius:12px;font-weight:800;
    text-decoration:none;font-size:.87rem;transition:all .15s;
  }
  .a-red{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.25);color:#f87171;}
  .a-pk{background:rgba(244,114,182,.1);border:1px solid rgba(244,114,182,.22);color:#f472b6;}
  .a-vi{background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.22);color:#a78bfa;}
  .tag{
    font-size:.6rem;font-weight:900;letter-spacing:2px;text-transform:uppercase;
    color:#34d399;display:flex;align-items:center;gap:5px;
  }
  .dot{width:5px;height:5px;border-radius:50%;background:#34d399;box-shadow:0 0 6px #34d399;}
</style>
</head>
<body>
  <div class="shield">🛡️</div>
  <div class="tag"><span class="dot"></span>Portal Seguro · Sentinel v9</div>
  <h1>Sin conexión a internet</h1>
  <p>
    No se puede conectar al servidor en este momento.<br>
    En caso de emergencia, usa estos números directamente:
  </p>
  <div class="em">
    <a href="tel:911" class="a-red">📞 Llamar al 911 · Emergencias</a>
    <a href="tel:5556581111" class="a-pk">👩 Línea Mujeres CDMX</a>
    <a href="tel:8008224460" class="a-vi">🏠 Red Nacional de Refugios</a>
  </div>
  <p style="font-size:.75rem;color:#5e5478;margin-top:8px;">
    Cuando recuperes conexión, la app se actualizará automáticamente.
  </p>
  <button
    onclick="location.reload()"
    style="background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);
           color:#a78bfa;padding:10px 22px;border-radius:9px;
           font-weight:800;font-size:.8rem;cursor:pointer;margin-top:4px;">
    🔄 Reintentar conexión
  </button>
</body>
</html>"""
    return HttpResponse(html)