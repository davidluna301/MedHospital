from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "accounts"

urlpatterns = [
    path("iniciar-sesion/", views.CustomLoginView.as_view(), name="login"),
    path("cerrar-sesion/", views.CustomLogoutView.as_view(), name="logout"),
    path(
        "registro/paciente/",
        RedirectView.as_view(pattern_name="consultas:home", permanent=False),
        name="registro_paciente",
    ),
    path(
        "registro/medico/",
        RedirectView.as_view(pattern_name="consultas:home", permanent=False),
        name="registro_medico",
    ),
]
