from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_torneos, name='torneos'),
    path('<int:torneo_id>/', views.detalle_torneo, name='detalle_torneo'),
    path('partida/<int:partida_id>/', views.detalle_partida, name='detalle_partida'),
    path('partida/<int:partida_id>/reportar/', views.reportar_resultado, name='reportar_resultado'),
]
