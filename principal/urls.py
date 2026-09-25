from django.urls import path
from . import views # El punto significa "importa las vistas de esta misma carpeta"

urlpatterns = [
    # Tu lobby actual
    path('', views.LobbyView.as_view(), name='lobby'),
    path('lobby/', views.LobbyView.as_view(), name='lobby_alias'),
    
    # Las rutas de la Barra Lateral (Todas apuntan a construcción por ahora)
    path('noticias/', views.en_construccion, name='noticias'),
    path('torneos/', views.en_construccion, name='torneos'),
    path('transmisiones/', views.en_construccion, name='transmisiones'),
    path('equipos/', views.en_construccion, name='equipos'),
    path('juegos/', views.en_construccion, name='juegos'),
    path('chat/', views.en_construccion, name='chat'),
    path('tienda/', views.en_construccion, name='tienda'),
    path('soporte/', views.en_construccion, name='soporte'),
    path('ranking/', views.vista_ranking, name='ranking'),
    
    # Rutas de botones especiales (Hero Banner y Perfil)
    path('marcar-leidas/', views.marcar_notificaciones_leidas, name='marcar_leidas'),
    
]