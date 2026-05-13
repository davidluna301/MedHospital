from datetime import time

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone as dj_tz

from .models import (
    Appointment,
    Doctor,
    DoctorAvailability,
    MedicalRecord,
    Patient,
    Specialty,
)

User = get_user_model()


class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ("nombre", "descripcion")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ("usuario", "especialidad", "cedula_profesional", "telefono", "biografia")
        widgets = {"biografia": forms.Textarea(attrs={"rows": 3})}

    def clean_usuario(self):
        u = self.cleaned_data["usuario"]
        if u.role != User.Role.MEDICO:
            raise ValidationError("El usuario debe tener rol Médico.")
        qs = Doctor.objects.filter(usuario=u)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este usuario ya tiene perfil de médico.")
        return u


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = (
            "usuario",
            "fecha_nacimiento",
            "tipo_sangre",
            "telefono",
            "contacto_emergencia",
            "numero_seguro",
        )

    def clean_usuario(self):
        u = self.cleaned_data["usuario"]
        if u.role != User.Role.PACIENTE:
            raise ValidationError("El usuario debe tener rol Paciente.")
        qs = Patient.objects.filter(usuario=u)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este usuario ya tiene perfil de paciente.")
        return u


class PacienteSelfForm(forms.ModelForm):
    """Perfil de paciente sin modificar el vínculo de usuario."""

    class Meta:
        model = Patient
        fields = (
            "fecha_nacimiento",
            "tipo_sangre",
            "telefono",
            "contacto_emergencia",
            "numero_seguro",
        )


class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = DoctorAvailability
        fields = ("medico", "dia_semana", "hora_inicio", "hora_fin")

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        inst = DoctorAvailability(**data)
        inst.clean()
        return data


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = (
            "paciente",
            "medico",
            "fecha_hora",
            "duracion_minutos",
            "estado",
            "motivo",
            "notas",
        )
        widgets = {
            "fecha_hora": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "notas": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)
        self.fields["fecha_hora"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ]
        if user and user.role == User.Role.MEDICO:
            try:
                doc = user.perfil_medico
            except Doctor.DoesNotExist:
                doc = None
            if doc:
                self.fields["medico"].queryset = Doctor.objects.filter(pk=doc.pk)
                self.fields["medico"].widget = forms.HiddenInput()
        if user and user.role == User.Role.PACIENTE:
            try:
                pac = user.perfil_paciente
            except Patient.DoesNotExist:
                pac = None
            if pac:
                self.fields["paciente"].queryset = Patient.objects.filter(pk=pac.pk)
                self.fields["paciente"].widget = forms.HiddenInput()
            self.fields["estado"].initial = Appointment.Estado.PROGRAMADA
            self.fields["estado"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        u = self._user
        if u and u.role == User.Role.PACIENTE:
            try:
                cleaned["paciente"] = u.perfil_paciente
            except Patient.DoesNotExist:
                raise ValidationError("No tiene perfil de paciente.")
            cleaned["estado"] = Appointment.Estado.PROGRAMADA
        if u and u.role == User.Role.MEDICO:
            try:
                cleaned["medico"] = u.perfil_medico
            except Doctor.DoesNotExist:
                raise ValidationError("No tiene perfil de médico.")

        fecha_hora = cleaned.get("fecha_hora")
        medico = cleaned.get("medico")
        if fecha_hora and medico:
            dt = dj_tz.localtime(fecha_hora)
            wd = dt.weekday()
            t = dt.time()
            slots = DoctorAvailability.objects.filter(medico=medico, dia_semana=wd)
            if slots.exists():
                ok = any(s.hora_inicio <= t < s.hora_fin for s in slots)
                if not ok:
                    raise ValidationError(
                        "La hora no está dentro de los horarios disponibles del médico."
                    )
            else:
                if not (time(8, 0) <= t <= time(18, 0)):
                    raise ValidationError(
                        "Sin horario definido: seleccione entre 08:00 y 18:00."
                    )

        m = Appointment(
            paciente=cleaned["paciente"],
            medico=cleaned["medico"],
            fecha_hora=cleaned["fecha_hora"],
            duracion_minutos=cleaned.get("duracion_minutos") or 30,
            estado=cleaned.get("estado") or Appointment.Estado.PROGRAMADA,
            motivo=cleaned.get("motivo") or "",
            notas=cleaned.get("notas") or "",
        )
        m.pk = self.instance.pk
        m.clean()
        return cleaned


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = (
            "paciente",
            "medico",
            "cita",
            "fecha_consulta",
            "diagnostico",
            "receta",
            "observaciones",
        )
        widgets = {
            "diagnostico": forms.Textarea(attrs={"rows": 3}),
            "receta": forms.Textarea(attrs={"rows": 3}),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)
        if user and user.role == User.Role.MEDICO:
            try:
                doc = user.perfil_medico
            except Doctor.DoesNotExist:
                doc = None
            if doc:
                self.fields["medico"].queryset = Doctor.objects.filter(pk=doc.pk)
                self.fields["medico"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        if self._user and self._user.role == User.Role.MEDICO:
            try:
                cleaned["medico"] = self._user.perfil_medico
            except Doctor.DoesNotExist:
                raise ValidationError("No tiene perfil de médico.")
        return cleaned


class AltaMedicoAdminForm(forms.Form):
    """Alta de médico con usuario (solo administrador)."""

    email = forms.EmailField(label="Correo")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    especialidad = forms.ModelChoiceField(
        label="Especialidad",
        queryset=Specialty.objects.none(),
    )
    cedula_profesional = forms.CharField(label="Cédula profesional", max_length=50)
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)
    biografia = forms.CharField(
        label="Biografía breve", widget=forms.Textarea(attrs={"rows": 3}), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["especialidad"].queryset = Specialty.objects.all().order_by("nombre")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean_cedula_profesional(self):
        ced = self.cleaned_data["cedula_profesional"].strip()
        if Doctor.objects.filter(cedula_profesional__iexact=ced).exists():
            raise ValidationError("Esta cédula ya está registrada.")
        return ced

    def clean(self):
        data = super().clean()
        if data.get("password1") and data.get("password2"):
            if data["password1"] != data["password2"]:
                raise ValidationError("Las contraseñas no coinciden.")
        return data


class AltaPacienteOperadorForm(forms.Form):
    """Alta de paciente con usuario (solo operador de atención)."""

    email = forms.EmailField(label="Correo")
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    fecha_nacimiento = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)
    tipo_sangre = forms.CharField(label="Tipo de sangre", max_length=5, required=False)
    contacto_emergencia = forms.CharField(
        label="Contacto de emergencia", max_length=120, required=False
    )
    numero_seguro = forms.CharField(
        label="Número de seguro", max_length=80, required=False
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean(self):
        data = super().clean()
        if data.get("password1") and data.get("password2"):
            if data["password1"] != data["password2"]:
                raise ValidationError("Las contraseñas no coinciden.")
        return data


class CitaCertificadoForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ("certificado", "certificado_notas")
        widgets = {
            "certificado": forms.ClearableFileInput(
                attrs={"accept": ".pdf,.png,.jpg,.jpeg", "class": "form-control"}
            ),
            "certificado_notas": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["certificado"].validators = [
            FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])
        ]
        self.fields["certificado"].required = False

    def clean_certificado(self):
        f = self.cleaned_data.get("certificado")
        if f and f.size > 4 * 1024 * 1024:
            raise ValidationError("El archivo no debe superar 4 MB.")
        return f
