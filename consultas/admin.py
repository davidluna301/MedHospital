from django.contrib import admin

# Registro de modelos en el sitio de administración Django.

from .models import (
    Appointment,
    Doctor,
    DoctorAvailability,
    MedicalRecord,
    Patient,
    Specialty,
)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)


class DoctorAvailabilityInline(admin.TabularInline):
    model = DoctorAvailability
    extra = 0


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "especialidad", "cedula_profesional", "telefono")
    list_filter = ("especialidad",)
    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "cedula_profesional",
    )
    inlines = [DoctorAvailabilityInline]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "fecha_nacimiento",
        "telefono",
        "tipo_sangre",
        "numero_seguro",
    )
    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "numero_seguro",
    )
    list_filter = ("tipo_sangre",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "paciente",
        "medico",
        "fecha_hora",
        "estado",
        "motivo",
        "certificado",
        "creado_en",
    )
    list_filter = ("estado", "fecha_hora", "medico__especialidad")
    search_fields = (
        "motivo",
        "paciente__usuario__first_name",
        "paciente__usuario__last_name",
        "medico__usuario__first_name",
    )
    date_hierarchy = "fecha_hora"
    raw_id_fields = ("paciente", "medico")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("paciente", "medico", "fecha_consulta", "diagnostico")
    list_filter = ("fecha_consulta", "medico__especialidad")
    search_fields = ("diagnostico", "paciente__usuario__last_name")
    raw_id_fields = ("paciente", "medico", "cita")
