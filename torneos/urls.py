from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_torneos, name='torneos'),
    path('<int:torneo_id>/', views.TorneoDetailView.as_view(), name='detalle_torneo'),
    path('<int:torneo_id>/inscribirse/', views.inscribir_equipo, name='inscribir_equipo'),
    path('mis-torneos/', views.MisTorneosView.as_view(), name='mis_torneos'),
    path('partida/<int:partida_id>/', views.SalaPartidaView.as_view(), name='detalle_partida'),
    path('partida/<int:partida_id>/reportar/', views.SalaPartidaView.as_view(), name='reportar_resultado'),
]
