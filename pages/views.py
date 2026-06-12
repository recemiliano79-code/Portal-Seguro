# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages


def login_register_view(request):
    """
    Vista única que maneja tanto el login como el registro
    en la misma página con tabs.
    Copia este archivo a: accounts/views.py
    Asegúrate de que accounts/urls.py tenga:
        path('login/', views.login_register_view, name='login'),
        path('register/', views.login_register_view, name='register'),
    """
    login_form = AuthenticationForm()
    register_form = UserCreationForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'login')

        if form_type == 'register':
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                # Agregar email si fue proporcionado
                email = request.POST.get('email', '').strip()
                if email:
                    user.email = email
                    user.save()
                # Login automático después del registro
                login(request, user)
                messages.success(request, f'¡Bienvenida, {user.username}! Tu cuenta ha sido creada.')
                return redirect('projects:home')
            else:
                # Si hay errores en registro, mostrar tab de registro
                return render(request, 'registration/login.html', {
                    'form': login_form,
                    'register_form': register_form,
                })

        else:  # form_type == 'login'
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                # Redirigir a 'next' si existe, si no al home
                next_url = request.GET.get('next', 'projects:home')
                return redirect(next_url if next_url != 'projects:home' else 'projects:home')
            else:
                return render(request, 'registration/login.html', {
                    'form': login_form,
                    'register_form': register_form,
                })

    return render(request, 'registration/login.html', {
        'form': login_form,
        'register_form': register_form,
    })


# ─────────────────────────────────────────────────────────────────────────────
# accounts/urls.py — reemplaza con esto:
# ─────────────────────────────────────────────────────────────────────────────
#
# from django.urls import path
# from . import views
#
# app_name = 'accounts'
#
# urlpatterns = [
#     path('login/', views.login_register_view, name='login'),
#     path('register/', views.login_register_view, name='register'),
# ]
#
# ─────────────────────────────────────────────────────────────────────────────
# proyecto_acoso/urls.py — asegúrate de que tenga:
# ─────────────────────────────────────────────────────────────────────────────
#
# from django.contrib.auth import views as auth_views
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('accounts/', include('accounts.urls')),   # ← tu app custom PRIMERO
#     path('accounts/', include('django.contrib.auth.urls')),  # ← django después
#     path('ai/', include('projects.ai_urls')),
#     path('', include('projects.urls')),
# ]
#
# ─────────────────────────────────────────────────────────────────────────────
# settings.py — asegúrate de tener:
# ─────────────────────────────────────────────────────────────────────────────
#
# LOGIN_REDIRECT_URL = '/'
# LOGIN_URL = '/accounts/login/'
# LOGOUT_REDIRECT_URL = '/accounts/login/'
#