"""
========================================
URLS PARA ENDPOINTS DE IA SENTINEL
========================================

Este módulo contiene todas las rutas URL necesarias para exponer
los endpoints de la API de IA Sentinel.

Autor: Proyecto Sentinel
Versión: 7.0
"""

from django.urls import path, re_path
from . import ai_views

app_name = 'ai'

urlpatterns = [
    # Endpoint principal de chat con IA
    path('chat/', ai_views.ai_chat_endpoint, name='chat'),
    
    # Endpoint para respuestas rápidas por tema
    path('quick/<str:topic>/', ai_views.ai_quick_response_endpoint, name='quick_response'),
    
    # Endpoint para información de emergencia
    path('emergency/', ai_views.get_emergency_info, name='emergency'),
    
    # Endpoint de verificación de salud del servicio
    path('health/', ai_views.health_check, name='health'),
    
    # Endpoint de chat con clase basada en vistas (alternativo)
    path('chat/v2/', ai_views.AIChatEndpoint.as_view(), name='chat_v2'),
    
    # Endpoint de emergencia con clase basada en vistas
    path('emergency/v2/', ai_views.EmergencyInfoEndpoint.as_view(), name='emergency_v2'),
]

# URLs adicionales para documentación y debugging (solo en desarrollo)
if True:  # Cambiar a settings.DEBUG en producción
    urlpatterns += [
        # Endpoint de información institucional
        path('resources/institutions/', 
             ai_views.get_emergency_info, 
             {'type': 'institutions'},
             name='resources_institutions'),
        
        # Endpoint de información legal
        path('resources/legal/', 
             ai_views.get_emergency_info, 
             {'type': 'legal'},
             name='resources_legal'),
        
        # Endpoint de tips de ciberseguridad
        path('resources/cibersecurity/', 
             ai_views.get_emergency_info, 
             {'type': 'ciber'},
             name='resources_cibersecurity'),
    ]