# ═══════════════════════════════════════════════════
#  accounts/views.py
#  Copia este archivo completo a:  accounts/views.py
# ═══════════════════════════════════════════════════

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages


def login_register_view(request):

    # ══════════════════════════════════════════════════════════
    #  FIX PRINCIPAL: si ya hay sesión activa → ir al dashboard
    #  Sin esto, Django entra directo sin pedir login
    # ══════════════════════════════════════════════════════════
    if request.user.is_authenticated:
        return redirect('projects:home')   # ← ESTE ES EL FIX

    login_form    = AuthenticationForm()
    register_form = UserCreationForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'login')

        # ── REGISTRO ─────────────────────────────────────────────
        if form_type == 'register':
            register_form = UserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                # Guardar email si fue proporcionado
                email = request.POST.get('email', '').strip()
                if email:
                    user.email = email
                    user.save()
                # Login automático después de registrarse
                login(request, user)
                messages.success(request, f'¡Bienvenida, {user.username}! Tu cuenta fue creada.')
                return redirect('projects:home')
            # Errores → mostrar tab de registro
            return render(request, 'registration/login.html', {
                'form':          login_form,
                'register_form': register_form,
                'active_tab':    'register',   # para mostrar tab correcto
            })

        # ── LOGIN ─────────────────────────────────────────────────
        else:
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                # Respetar ?next= si existe
                next_url = request.GET.get('next', '')
                return redirect(next_url if next_url else 'projects:home')
            # Errores → mostrar tab de login
            return render(request, 'registration/login.html', {
                'form':          login_form,
                'register_form': register_form,
                'active_tab':    'login',
            })

    # GET normal
    return render(request, 'registration/login.html', {
        'form':          login_form,
        'register_form': register_form,
        'active_tab':    'login',
    })