# ═══════════════════════════════════════════════════
#  accounts/urls.py
#  Copia este archivo completo a:  accounts/urls.py
# ═══════════════════════════════════════════════════

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',    views.login_register_view, name='login'),
    path('register/', views.login_register_view, name='register'),
]