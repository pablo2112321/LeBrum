from django.urls import path
from . import views # El punto significa "importa las vistas de esta misma carpeta"
from usuarios import views as usuarios_views

urlpatterns = [
    # Tu lobby actual
    path('', views.LobbyView.as_view(), name='lobby'),
    path('lobby/', views.LobbyView.as_view(), name='lobby_alias'),
    
    # Las rutas de la Barra Lateral (Todas apuntan a construcción por ahora)
    path('noticias/', views.NoticiasView.as_view(), name='noticias'),
    path('torneos/', views.en_construccion, name='torneos'),
    path('transmisiones/', views.TransmisionesView.as_view(), name='transmisiones'),
    path('equipos/', views.en_construccion, name='equipos'),
    path('juegos/', views.JuegosView.as_view(), name='juegos'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('tienda/', views.TiendaView.as_view(), name='tienda'),
    path('soporte/', views.en_construccion, name='soporte'),
    path('ranking/', usuarios_views.RankingView.as_view(), name='ranking'),
    
    # Rutas de botones especiales (Hero Banner y Perfil)
    path('marcar-leidas/', views.marcar_notificaciones_leidas, name='marcar_leidas'),
    
]