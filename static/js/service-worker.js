══════════════════════════════════════════════════════════
  PORTAL SEGURO · GUÍA COMPLETA PWA
  Convierte tu app Django en app instalable (Android + iOS)
══════════════════════════════════════════════════════════

IMPORTANTE: Las PWA requieren HTTPS para funcionar.
No funcionan en http://localhost — necesitas subirla primero.
Pero puedes preparar todo ahora y probar cuando esté online.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 1 — GENERA LOS ÍCONOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Copia generate_icons.py a la raíz de tu proyecto:
   C:\Users\RICARDO\acoso_sexualgre\generate_icons.py

2. Instala Pillow (si no lo tienes):
   pip install Pillow

3. Ejecuta:
   python generate_icons.py

   Esto creará: static/icons/icon-72.png, icon-96.png... icon-512.png


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 2 — COPIA LOS ARCHIVOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estructura de archivos a crear:

acoso_sexualgre/
├── static/
│   ├── icons/
│   │   ├── icon-72.png    ← generado en paso 1
│   │   ├── icon-96.png
│   │   ├── icon-128.png
│   │   ├── icon-144.png
│   │   ├── icon-152.png
│   │   ├── icon-192.png
│   │   ├── icon-384.png
│   │   └── icon-512.png
│   └── js/
│       └── service-worker.js   ← copiar service-worker.js aquí
│
├── projects/
│   └── pwa_views.py            ← copiar pwa_views.py aquí
│
├── proyecto_acoso/
│   └── urls.py                 ← modificar (ver paso 3)
│
└── projects/templates/projects/
    └── base_dashboard.html     ← modificar (ver paso 4)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 3 — MODIFICA urls.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Abre proyecto_acoso/urls.py y agrega al principio:

    from projects.pwa_views import service_worker, manifest, offline

Luego al inicio de urlpatterns (ANTES de las otras rutas):

    urlpatterns = [
        path('service-worker.js', service_worker, name='service-worker'),
        path('manifest.json',     manifest,       name='manifest'),
        path('offline/',          offline,         name='offline'),
        path('admin/', admin.site.urls),
        path('accounts/', include('accounts.urls')),
        ...resto igual...
    ]


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 4 — MODIFICA base_dashboard.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Abre el archivo pwa_head_snippet.html y copia su contenido en DOS partes:

A) El bloque de meta tags (todo lo que está antes del segundo ══)
   → Pégalo dentro del <head> de base_dashboard.html
   → Justo después de las líneas de Google Fonts

B) El bloque <script> con el Service Worker registration
   → Pégalo justo antes del </body> de base_dashboard.html
   → Después de los demás <script>


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 5 — SUBE A RENDER.COM (GRATIS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Las PWA necesitan HTTPS. Render.com lo da gratis:

1. Crea cuenta en https://render.com

2. Crea un requirements.txt con:
   django==5.2.7
   pymysql
   gunicorn
   pillow
   whitenoise

3. Crea un Procfile (sin extensión) con:
   web: gunicorn proyecto_acoso.wsgi:application

4. Agrega a settings.py:
   ALLOWED_HOSTS = ['*']
   STATIC_ROOT = BASE_DIR / 'staticfiles'

   # WhiteNoise para servir archivos estáticos:
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       ...resto...
   ]
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

5. Ejecuta:
   python manage.py collectstatic

6. Sube todo a GitHub (repo privado está bien)

7. En Render: New → Web Service → conecta tu repo
   - Build Command: pip install -r requirements.txt && python manage.py collectstatic --noinput
   - Start Command: gunicorn proyecto_acoso.wsgi:application
   - Environment: Python 3

8. Render te da una URL tipo: https://portal-seguro.onrender.com
   ¡Ya tiene HTTPS automático!


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PASO 6 — INSTALAR COMO APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EN ANDROID (Chrome):
  1. Abre tu URL en Chrome
  2. Aparece banner "Agregar a pantalla de inicio"
  3. O: menú (⋮) → "Agregar a pantalla de inicio"
  4. ¡La app aparece en tu homescreen como ícono!

EN iOS (Safari):
  1. Abre tu URL en Safari (NO Chrome en iOS)
  2. Toca el botón Compartir (□↑)
  3. "Agregar a pantalla de inicio"
  4. ¡Aparece como app con ícono propio!

EN COMPUTADORA (Chrome/Edge):
  1. Abre la URL
  2. Ícono de instalar en la barra de dirección (⊕)
  3. Click → "Instalar"


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VERIFICAR QUE FUNCIONA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

En Chrome DevTools (F12):
  → Pestaña "Application"
  → "Service Workers" → debe mostrar tu SW activo ✓
  → "Manifest" → debe mostrar todos los íconos ✓
  → "Lighthouse" → ejecuta auditoría PWA → busca puntaje verde ✓


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESUMEN DE ARCHIVOS A COPIAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

service-worker.js  → static/js/service-worker.js
pwa_views.py       → projects/pwa_views.py
pwa_head_snippet.html → partes van en base_dashboard.html
generate_icons.py  → raíz del proyecto (ejecutar una vez)
manifest.json      → solo referencia, se genera dinámicamente

══════════════════════════════════════════════════════════
  ¡Con esto tu Portal Seguro es una app instalable! 🛡️
══════════════════════════════════════════════════════════