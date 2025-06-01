from django.urls import path
from . import views

app_name = 'core'  # Namespace pour les URLs de cette application

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_simple, name='login'),
    path('logout/', views.logout_simple, name='logout'),

]