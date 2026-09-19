from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_equipos, name='equipos'),
    path('crear/', views.crear_equipo, name='crear_equipo'),
    path('<int:equipo_id>/', views.detalle_equipo, name='detalle_equipo'),
    path('<int:equipo_id>/unirse/', views.unirse_equipo, name='unirse_equipo'),
    path('<int:equipo_id>/expulsar/<int:usuario_id>/', views.expulsar_miembro, name='expulsar_miembro'),
]
