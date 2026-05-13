from functools import wraps

from django import forms as django_forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone as dj_tz
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from accounts.models import User

from .certificados import constancia_cita_pdf_response
from .forms import (
    AltaMedicoAdminForm,
    AltaPacienteOperadorForm,
    AppointmentForm,
    CitaCertificadoForm,
    DoctorAvailabilityForm,
    DoctorForm,
    MedicalRecordForm,
    PacienteSelfForm,
    PatientForm,
    SpecialtyForm,
)
from .models import (
    Appointment,
    Doctor,
    DoctorAvailability,
    MedicalRecord,
    Patient,
    Specialty,
)
from .reports import exportar_citas_excel, exportar_citas_pdf


def role_required(*roles):
    def decorator(view_fn):
        @wraps(view_fn)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            if request.user.role not in roles:
                messages.error(request, "No tiene permiso para acceder a esta sección.")
                return redirect("consultas:panel")
            return view_fn(request, *args, **kwargs)

        return _wrapped

    return decorator


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == User.Role.ADMIN


class MedicoOAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in (
            User.Role.ADMIN,
            User.Role.MEDICO,
        )


class OperadorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role == User.Role.OPERADOR
        )


@login_required
def panel(request):
    user = request.user
    ctx = {"ahora": dj_tz.now()}
    if user.role == User.Role.ADMIN:
        ctx.update(
            {
                "total_citas": Appointment.objects.count(),
                "total_pacientes": Patient.objects.count(),
                "total_medicos": Doctor.objects.count(),
                "total_especialidades": Specialty.objects.count(),
                "citas_recientes": Appointment.objects.select_related(
                    "paciente__usuario", "medico__usuario"
                ).order_by("-creado_en")[:8],
                "mostrar_graficos": True,
            }
        )
    elif user.role == User.Role.MEDICO:
        doc = getattr(user, "perfil_medico", None)
        if doc:
            ctx.update(
                {
                    "total_citas": Appointment.objects.filter(medico=doc).count(),
                    "citas_recientes": Appointment.objects.filter(medico=doc)
                    .select_related("paciente__usuario")
                    .order_by("-fecha_hora")[:8],
                    "medico": doc,
                }
            )
        else:
            messages.warning(request, "Complete su perfil de médico con un administrador.")
            ctx["citas_recientes"] = []
            ctx["total_citas"] = 0
    elif user.role == User.Role.OPERADOR:
        ctx.update(
            {
                "total_citas": Appointment.objects.count(),
                "total_pacientes": Patient.objects.count(),
                "citas_recientes": Appointment.objects.select_related(
                    "paciente__usuario", "medico__usuario"
                ).order_by("-creado_en")[:8],
            }
        )
    elif user.role == User.Role.PACIENTE:
        pac = getattr(user, "perfil_paciente", None)
        if pac:
            ctx.update(
                {
                    "mis_citas": Appointment.objects.filter(paciente=pac)
                    .select_related("medico__usuario", "medico__especialidad")
                    .order_by("-fecha_hora")[:10],
                }
            )
        else:
            ctx["mis_citas"] = []
    else:
        ctx["mis_citas"] = []
    return render(request, "consultas/panel.html", ctx)


@login_required
@role_required(User.Role.ADMIN)
def chart_citas_por_especialidad(request):
    rows = (
        Appointment.objects.values("medico__especialidad__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    labels = [r["medico__especialidad__nombre"] or "—" for r in rows]
    values = [r["total"] for r in rows]
    return JsonResponse({"labels": labels, "values": values})


@login_required
@role_required(User.Role.ADMIN)
def chart_pacientes_nuevos_mes(request):
    rows = (
        Patient.objects.annotate(mes=TruncMonth("usuario__date_joined"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )
    labels = []
    values = []
    for r in rows:
        m = r["mes"]
        labels.append(m.strftime("%Y-%m") if m else "—")
        values.append(r["total"])
    return JsonResponse({"labels": labels, "values": values})


@login_required
@role_required(User.Role.ADMIN, User.Role.MEDICO, User.Role.OPERADOR)
def export_citas_pdf(request):
    return exportar_citas_pdf(request)


@login_required
@role_required(User.Role.ADMIN, User.Role.MEDICO, User.Role.OPERADOR)
def export_citas_excel(request):
    return exportar_citas_excel(request)


def _citas_queryset(request):
    qs = Appointment.objects.select_related(
        "paciente__usuario", "medico__usuario", "medico__especialidad"
    )
    user = request.user
    if user.role == User.Role.PACIENTE:
        try:
            qs = qs.filter(paciente=user.perfil_paciente)
        except Patient.DoesNotExist:
            qs = qs.none()
    elif user.role == User.Role.MEDICO:
        try:
            qs = qs.filter(medico=user.perfil_medico)
        except Doctor.DoesNotExist:
            qs = qs.none()
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")
    estado = request.GET.get("estado")
    if desde:
        qs = qs.filter(fecha_hora__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_hora__date__lte=hasta)
    if estado:
        qs = qs.filter(estado=estado)
    return qs.order_by("-fecha_hora")


@login_required
def cita_list(request):
    return render(
        request,
        "consultas/cita_list.html",
        {"object_list": _citas_queryset(request), "filtros": request.GET},
    )


@login_required
def cita_create(request):
    if request.user.role not in (
        User.Role.ADMIN,
        User.Role.MEDICO,
        User.Role.PACIENTE,
        User.Role.OPERADOR,
    ):
        messages.error(request, "No puede crear citas.")
        return redirect("consultas:cita_list")
    if request.method == "POST":
        form = AppointmentForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cita registrada correctamente.")
            return redirect("consultas:cita_list")
    else:
        initial = {}
        if request.user.role == User.Role.MEDICO:
            try:
                initial["medico"] = request.user.perfil_medico.pk
            except Doctor.DoesNotExist:
                pass
        if request.user.role == User.Role.PACIENTE:
            try:
                initial["paciente"] = request.user.perfil_paciente.pk
            except Patient.DoesNotExist:
                pass
        form = AppointmentForm(user=request.user, initial=initial)
    return render(request, "consultas/cita_form.html", {"form": form, "titulo": "Nueva cita"})


@login_required
def cita_update(request, pk):
    cita = get_object_or_404(Appointment, pk=pk)
    if request.user.role == User.Role.PACIENTE:
        messages.warning(
            request,
            "Los pacientes no pueden modificar citas aquí. Use «Certificado» o «Constancia» en el listado de sus citas.",
        )
        return redirect("consultas:cita_list")
    if request.user.role == User.Role.MEDICO:
        if cita.medico_id != getattr(
            getattr(request.user, "perfil_medico", None), "pk", None
        ):
            messages.error(request, "No autorizado.")
            return redirect("consultas:cita_list")
    elif request.user.role not in (User.Role.ADMIN, User.Role.OPERADOR):
        messages.error(request, "No autorizado.")
        return redirect("consultas:cita_list")
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=cita, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cita actualizada.")
            return redirect("consultas:cita_list")
    else:
        form = AppointmentForm(instance=cita, user=request.user)
    return render(
        request,
        "consultas/cita_form.html",
        {"form": form, "titulo": f"Editar cita #{cita.pk}"},
    )


@login_required
def cita_delete(request, pk):
    cita = get_object_or_404(Appointment, pk=pk)
    if request.user.role not in (User.Role.ADMIN, User.Role.MEDICO):
        messages.error(request, "Solo personal autorizado puede eliminar citas.")
        return redirect("consultas:cita_list")
    if request.user.role == User.Role.MEDICO and cita.medico_id != getattr(
        getattr(request.user, "perfil_medico", None), "pk", None
    ):
        messages.error(request, "No autorizado.")
        return redirect("consultas:cita_list")
    if request.method == "POST":
        cita.delete()
        messages.success(request, "Cita eliminada.")
        return redirect("consultas:cita_list")
    return render(request, "consultas/cita_confirm_delete.html", {"object": cita})


class SpecialtyList(AdminRequiredMixin, ListView):
    model = Specialty
    template_name = "consultas/especialidad_list.html"
    context_object_name = "object_list"


class SpecialtyCreate(AdminRequiredMixin, CreateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = "consultas/especialidad_form.html"
    success_url = reverse_lazy("consultas:especialidad_list")


class SpecialtyUpdate(AdminRequiredMixin, UpdateView):
    model = Specialty
    form_class = SpecialtyForm
    template_name = "consultas/especialidad_form.html"
    success_url = reverse_lazy("consultas:especialidad_list")


class SpecialtyDelete(AdminRequiredMixin, DeleteView):
    model = Specialty
    template_name = "consultas/especialidad_confirm_delete.html"
    success_url = reverse_lazy("consultas:especialidad_list")


class DoctorList(AdminRequiredMixin, ListView):
    model = Doctor
    template_name = "consultas/doctor_list.html"
    context_object_name = "object_list"


class DoctorRegistroAdminView(AdminRequiredMixin, FormView):
    template_name = "consultas/medico_alta_form.html"
    form_class = AltaMedicoAdminForm
    success_url = reverse_lazy("consultas:doctor_list")

    def form_valid(self, form):
        u = User.objects.create_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            role=User.Role.MEDICO,
        )
        Doctor.objects.create(
            usuario=u,
            especialidad=form.cleaned_data["especialidad"],
            cedula_profesional=form.cleaned_data["cedula_profesional"],
            telefono=form.cleaned_data.get("telefono") or "",
            biografia=form.cleaned_data.get("biografia") or "",
        )
        messages.success(self.request, "Médico registrado correctamente.")
        return super().form_valid(form)


class DoctorUpdate(AdminRequiredMixin, UpdateView):
    model = Doctor
    form_class = DoctorForm
    template_name = "consultas/doctor_form.html"
    success_url = reverse_lazy("consultas:doctor_list")


class DoctorDelete(AdminRequiredMixin, DeleteView):
    model = Doctor
    template_name = "consultas/doctor_confirm_delete.html"
    success_url = reverse_lazy("consultas:doctor_list")


class PatientList(LoginRequiredMixin, ListView):
    model = Patient
    template_name = "consultas/paciente_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = super().get_queryset().select_related("usuario")
        if self.request.user.role == User.Role.PACIENTE:
            try:
                return qs.filter(pk=self.request.user.perfil_paciente.pk)
            except Patient.DoesNotExist:
                return qs.none()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(usuario__first_name__icontains=q)
                | Q(usuario__last_name__icontains=q)
                | Q(usuario__email__icontains=q)
                | Q(numero_seguro__icontains=q)
            )
        return qs.order_by("usuario__last_name")


class PatientDetail(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = "consultas/paciente_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == User.Role.PACIENTE:
            obj = get_object_or_404(Patient, pk=kwargs.get("pk"))
            try:
                if obj.pk != request.user.perfil_paciente.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:paciente_list")
            except Patient.DoesNotExist:
                return redirect("consultas:paciente_list")
        return super().dispatch(request, *args, **kwargs)


class OperadorPacienteRegistroView(OperadorRequiredMixin, FormView):
    template_name = "consultas/operador_paciente_alta.html"
    form_class = AltaPacienteOperadorForm
    success_url = reverse_lazy("consultas:paciente_list")

    def form_valid(self, form):
        u = User.objects.create_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            role=User.Role.PACIENTE,
        )
        Patient.objects.create(
            usuario=u,
            fecha_nacimiento=form.cleaned_data["fecha_nacimiento"],
            telefono=form.cleaned_data.get("telefono") or "",
            tipo_sangre=form.cleaned_data.get("tipo_sangre") or "",
            contacto_emergencia=form.cleaned_data.get("contacto_emergencia") or "",
            numero_seguro=form.cleaned_data.get("numero_seguro") or "",
        )
        messages.success(self.request, "Paciente registrado correctamente.")
        return super().form_valid(form)


class PatientUpdate(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "consultas/paciente_form.html"

    def get_form_class(self):
        if self.request.user.role == User.Role.PACIENTE:
            return PacienteSelfForm
        if self.request.user.role == User.Role.OPERADOR:
            return PacienteSelfForm
        return PatientForm

    def get_success_url(self):
        return reverse("consultas:paciente_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == User.Role.PACIENTE:
            try:
                if int(kwargs.get("pk")) != request.user.perfil_paciente.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:paciente_list")
            except (Patient.DoesNotExist, TypeError, ValueError):
                return redirect("consultas:paciente_list")
        elif request.user.role == User.Role.OPERADOR:
            pass
        elif request.user.role != User.Role.ADMIN:
            messages.error(request, "No autorizado.")
            return redirect("consultas:paciente_list")
        return super().dispatch(request, *args, **kwargs)


class PatientDelete(AdminRequiredMixin, DeleteView):
    model = Patient
    template_name = "consultas/paciente_confirm_delete.html"
    success_url = reverse_lazy("consultas:paciente_list")


class MedicalRecordList(LoginRequiredMixin, ListView):
    model = MedicalRecord
    template_name = "consultas/historia_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = super().get_queryset().select_related("paciente__usuario", "medico__usuario")
        u = self.request.user
        if u.role == User.Role.OPERADOR:
            return qs.none()
        if u.role == User.Role.MEDICO:
            try:
                return qs.filter(medico=u.perfil_medico).order_by("-fecha_consulta")
            except Doctor.DoesNotExist:
                return qs.none()
        if u.role == User.Role.PACIENTE:
            try:
                return qs.filter(paciente=u.perfil_paciente).order_by("-fecha_consulta")
            except Patient.DoesNotExist:
                return qs.none()
        return qs.order_by("-fecha_consulta")


class MedicalRecordDetail(LoginRequiredMixin, DetailView):
    model = MedicalRecord
    template_name = "consultas/historia_detail.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role == User.Role.OPERADOR:
            messages.error(request, "Las historias clínicas no están disponibles para su rol.")
            return redirect("consultas:panel")
        obj = get_object_or_404(MedicalRecord, pk=kwargs.get("pk"))
        u = request.user
        if u.role == User.Role.PACIENTE:
            try:
                if obj.paciente_id != u.perfil_paciente.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:historia_list")
            except Patient.DoesNotExist:
                return redirect("consultas:historia_list")
        elif u.role == User.Role.MEDICO:
            try:
                if obj.medico_id != u.perfil_medico.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:historia_list")
            except Doctor.DoesNotExist:
                return redirect("consultas:historia_list")
        return super().dispatch(request, *args, **kwargs)


class MedicalRecordCreate(MedicoOAdminMixin, CreateView):
    model = MedicalRecord
    form_class = MedicalRecordForm
    template_name = "consultas/historia_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, "Historia clínica creada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("consultas:historia_list")


class MedicalRecordUpdate(MedicoOAdminMixin, UpdateView):
    model = MedicalRecord
    form_class = MedicalRecordForm
    template_name = "consultas/historia_form.html"

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        obj = get_object_or_404(MedicalRecord, pk=pk)
        if request.user.role == User.Role.MEDICO:
            try:
                if obj.medico_id != request.user.perfil_medico.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:historia_list")
            except Doctor.DoesNotExist:
                return redirect("consultas:historia_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Historia actualizada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("consultas:historia_list")


class MedicalRecordDelete(MedicoOAdminMixin, DeleteView):
    model = MedicalRecord
    template_name = "consultas/historia_confirm_delete.html"
    success_url = reverse_lazy("consultas:historia_list")

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        obj = get_object_or_404(MedicalRecord, pk=pk)
        if request.user.role == User.Role.MEDICO:
            try:
                if obj.medico_id != request.user.perfil_medico.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:historia_list")
            except Doctor.DoesNotExist:
                return redirect("consultas:historia_list")
        return super().dispatch(request, *args, **kwargs)


class AvailabilityList(LoginRequiredMixin, ListView):
    model = DoctorAvailability
    template_name = "consultas/horario_list.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = super().get_queryset().select_related("medico__usuario")
        if self.request.user.role == User.Role.MEDICO:
            try:
                return qs.filter(medico=self.request.user.perfil_medico)
            except Doctor.DoesNotExist:
                return qs.none()
        if self.request.user.role in (User.Role.PACIENTE, User.Role.OPERADOR):
            return qs.none()
        return qs


class AvailabilityCreate(MedicoOAdminMixin, CreateView):
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = "consultas/horario_form.html"

    def get_initial(self):
        ini = super().get_initial()
        if self.request.user.role == User.Role.MEDICO:
            try:
                ini["medico"] = self.request.user.perfil_medico
            except Doctor.DoesNotExist:
                pass
        return ini

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == User.Role.MEDICO:
            try:
                form.fields["medico"].queryset = Doctor.objects.filter(
                    pk=self.request.user.perfil_medico.pk
                )
                form.fields["medico"].widget = django_forms.HiddenInput()
            except Doctor.DoesNotExist:
                pass
        return form

    def form_valid(self, form):
        if self.request.user.role == User.Role.MEDICO:
            form.instance.medico = self.request.user.perfil_medico
        messages.success(self.request, "Horario guardado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("consultas:horario_list")


class AvailabilityUpdate(MedicoOAdminMixin, UpdateView):
    model = DoctorAvailability
    form_class = DoctorAvailabilityForm
    template_name = "consultas/horario_form.html"
    success_url = reverse_lazy("consultas:horario_list")

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        obj = get_object_or_404(DoctorAvailability, pk=pk)
        if request.user.role == User.Role.MEDICO:
            try:
                if obj.medico_id != request.user.perfil_medico.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:horario_list")
            except Doctor.DoesNotExist:
                return redirect("consultas:horario_list")
        return super().dispatch(request, *args, **kwargs)


class AvailabilityDelete(MedicoOAdminMixin, DeleteView):
    model = DoctorAvailability
    template_name = "consultas/horario_confirm_delete.html"
    success_url = reverse_lazy("consultas:horario_list")

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        obj = get_object_or_404(DoctorAvailability, pk=pk)
        if request.user.role == User.Role.MEDICO:
            try:
                if obj.medico_id != request.user.perfil_medico.pk:
                    messages.error(request, "No autorizado.")
                    return redirect("consultas:horario_list")
            except Doctor.DoesNotExist:
                return redirect("consultas:horario_list")
        return super().dispatch(request, *args, **kwargs)


@login_required
def cita_certificado(request, pk):
    cita = get_object_or_404(
        Appointment.objects.select_related(
            "paciente__usuario", "medico__usuario", "medico__especialidad"
        ),
        pk=pk,
    )
    if request.user.role != User.Role.PACIENTE:
        messages.error(
            request,
            "Solo los pacientes pueden adjuntar o modificar el certificado de sus citas.",
        )
        return redirect("consultas:cita_list")
    try:
        if cita.paciente_id != request.user.perfil_paciente_id:
            messages.error(request, "No autorizado.")
            return redirect("consultas:cita_list")
    except Patient.DoesNotExist:
        return redirect("consultas:cita_list")
    if cita.estado not in (
        Appointment.Estado.CONFIRMADA,
        Appointment.Estado.COMPLETADA,
    ):
        messages.warning(
            request,
            "Solo puede guardar certificado cuando la cita está confirmada o completada.",
        )
        return redirect("consultas:cita_list")
    if request.method == "POST":
        form = CitaCertificadoForm(request.POST, request.FILES, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, "Certificado actualizado.")
            return redirect("consultas:cita_list")
    else:
        form = CitaCertificadoForm(instance=cita)
    return render(
        request,
        "consultas/cita_certificado.html",
        {"cita": cita, "form": form},
    )


@login_required
def cita_constancia_pdf(request, pk):
    cita = get_object_or_404(
        Appointment.objects.select_related(
            "paciente__usuario", "medico__usuario", "medico__especialidad"
        ),
        pk=pk,
    )
    if request.user.role != User.Role.PACIENTE:
        messages.error(request, "No autorizado.")
        return redirect("consultas:cita_list")
    try:
        if cita.paciente_id != request.user.perfil_paciente_id:
            messages.error(request, "No autorizado.")
            return redirect("consultas:cita_list")
    except Patient.DoesNotExist:
        return redirect("consultas:cita_list")
    if cita.estado == Appointment.Estado.CANCELADA:
        messages.warning(request, "No hay constancia para citas canceladas.")
        return redirect("consultas:cita_list")
    return constancia_cita_pdf_response(cita)
