from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}),
    )
