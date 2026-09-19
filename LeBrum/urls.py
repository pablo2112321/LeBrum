from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin-secreto/', admin.site.urls),

    path('login/', usuarios_views.login_view, name='login'),
    path('registro/', usuarios_views.registro_view, name='registro'),
    path('logout/', usuarios_views.logout_usuario, name='logout'),
    path('ojo-de-halcon/', usuarios_views.ojo_de_halcon, name='ojo_de_halcon'),
    path('redireccionar-segun-rol/', usuarios_views.redireccionar_segun_rol, name='redireccionar_segun_rol'),
    path('verificar-usuario/', usuarios_views.verificar_usuario, name='verificar_usuario'),
    path('verificar-tag/', usuarios_views.verificar_tag, name='verificar_tag'),

    path('equipos/', include('equipos.urls')),
    path('torneos/', include('torneos.urls')),
    path('', include('principal.urls')),
    path('usuarios/', include('usuarios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
