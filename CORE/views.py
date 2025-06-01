from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages


# Décorateur pour l'identification sur simple mot de passe :
def simple_auth_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated', False):
            return redirect('core:login')  # correspond au nom dans urls.py
        return view_func(request, *args, **kwargs)
    return wrapper


# PAGE D'ACCUEIL DE L'APPLICATION :
@simple_auth_required
def index(request):
    return render(request, 'core/index.html')


# LOGIN DE CONNEXION PAR SIMPLE MOT DE PASSE :
def login_simple(request):
    if request.method == "POST":
        password = request.POST.get("password")
        if password == settings.SIMPLE_APP_PASSWORD:
            request.session['authenticated'] = True
            return redirect('core:index')  # ou toute autre page d'accueil
        else:
            messages.error(request, "Mot de passe incorrect.")
    return render(request, 'core/login_simple.html')


# DECONNEXION DE LA SESSION :
def logout_simple(request):
    request.session.flush()  # Efface toutes les données de session
    return redirect('core:login')







