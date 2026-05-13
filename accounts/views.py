from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import EmailLoginForm


class LandingView(TemplateView):
    template_name = "home.html"


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("consultas:home")
