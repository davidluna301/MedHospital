from django.urls import path

from accounts.views import LandingView

from . import views

app_name = "consultas"

urlpatterns = [
    path("", LandingView.as_view(), name="home"),
    path("panel/", views.panel, name="panel"),
    path("api/chart/citas-especialidad/", views.chart_citas_por_especialidad, name="chart_citas_especialidad"),
    path("api/chart/pacientes-mes/", views.chart_pacientes_nuevos_mes, name="chart_pacientes_mes"),
    path("reportes/citas.pdf", views.export_citas_pdf, name="export_citas_pdf"),
    path("reportes/citas.xlsx", views.export_citas_excel, name="export_citas_excel"),
    path("citas/", views.cita_list, name="cita_list"),
    path("citas/nueva/", views.cita_create, name="cita_create"),
    path("citas/<int:pk>/certificado/", views.cita_certificado, name="cita_certificado"),
    path("citas/<int:pk>/constancia.pdf", views.cita_constancia_pdf, name="cita_constancia_pdf"),
    path("citas/<int:pk>/editar/", views.cita_update, name="cita_update"),
    path("citas/<int:pk>/eliminar/", views.cita_delete, name="cita_delete"),
    path("especialidades/", views.SpecialtyList.as_view(), name="especialidad_list"),
    path("especialidades/nueva/", views.SpecialtyCreate.as_view(), name="especialidad_create"),
    path("especialidades/<int:pk>/editar/", views.SpecialtyUpdate.as_view(), name="especialidad_update"),
    path("especialidades/<int:pk>/eliminar/", views.SpecialtyDelete.as_view(), name="especialidad_delete"),
    path("medicos/", views.DoctorList.as_view(), name="doctor_list"),
    path("medicos/nuevo/", views.DoctorRegistroAdminView.as_view(), name="doctor_create"),
    path("medicos/<int:pk>/editar/", views.DoctorUpdate.as_view(), name="doctor_update"),
    path("medicos/<int:pk>/eliminar/", views.DoctorDelete.as_view(), name="doctor_delete"),
    path("pacientes/", views.PatientList.as_view(), name="paciente_list"),
    path("pacientes/<int:pk>/", views.PatientDetail.as_view(), name="paciente_detail"),
    path("pacientes/nuevo/", views.OperadorPacienteRegistroView.as_view(), name="paciente_create"),
    path("pacientes/<int:pk>/editar/", views.PatientUpdate.as_view(), name="paciente_update"),
    path("pacientes/<int:pk>/eliminar/", views.PatientDelete.as_view(), name="paciente_delete"),
    path("historias/", views.MedicalRecordList.as_view(), name="historia_list"),
    path("historias/<int:pk>/", views.MedicalRecordDetail.as_view(), name="historia_detail"),
    path("historias/nueva/", views.MedicalRecordCreate.as_view(), name="historia_create"),
    path("historias/<int:pk>/editar/", views.MedicalRecordUpdate.as_view(), name="historia_update"),
    path("historias/<int:pk>/eliminar/", views.MedicalRecordDelete.as_view(), name="historia_delete"),
    path("horarios/", views.AvailabilityList.as_view(), name="horario_list"),
    path("horarios/nuevo/", views.AvailabilityCreate.as_view(), name="horario_create"),
    path("horarios/<int:pk>/editar/", views.AvailabilityUpdate.as_view(), name="horario_update"),
    path("horarios/<int:pk>/eliminar/", views.AvailabilityDelete.as_view(), name="horario_delete"),
]
