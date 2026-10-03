from django.urls import path
from . import views

urlpatterns = [
    # Las rutas del panel las dejamos apagadas (comentadas con #) por ahora
    # path('panel/', views.dashboard_principal, name='panel_dashboard'),
    # path('panel/', views.panel_control, name='panel_control'),
    # path('panel/cambiar-rol/<int:user_id>/', views.cambiar_rol_usuario, name='cambiar_rol'),
    
    path('panel/', views.panel_control, name='panel_control'),
    path('perfil/', views.perfil_redirect, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<str:nametag>/', views.PerfilDetalleView.as_view(), name='perfil_detalle'),
    path('perfil-buscar/', views.buscar_jugador, name='buscar_jugador'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('privacidad/exportar/', views.exportar_datos, name='exportar_datos'),
    path('privacidad/solicitar/', views.solicitar_privacidad, name='solicitar_privacidad'),
    path(
        'privacidad/solicitudes/<int:solicitud_id>/procesar/',
        views.procesar_privacidad,
        name='procesar_privacidad',
    ),
    path(
        'notificaciones/marcar-leidas/',
        views.MarcarNotificacionesLeidasView.as_view(),
        name='marcar_notificaciones_leidas',
    ),
    path('logout/', views.logout_usuario, name='logout'),
]