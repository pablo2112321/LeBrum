from django.urls import path

from . import views

app_name = 'soporte'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('nuevo/', views.ticket_create, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
]
