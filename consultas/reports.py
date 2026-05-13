"""Generación de reportes PDF (reportlab) y Excel (openpyxl) para citas filtradas."""
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone as dj_tz
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .models import Appointment, Doctor, Patient

User = get_user_model()


def _filtro_citas(request):
    qs = Appointment.objects.select_related("paciente__usuario", "medico__usuario")
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        if user.role == User.Role.MEDICO:
            try:
                qs = qs.filter(medico=user.perfil_medico)
            except Doctor.DoesNotExist:
                qs = qs.none()
        elif user.role == User.Role.PACIENTE:
            try:
                qs = qs.filter(paciente=user.perfil_paciente)
            except Patient.DoesNotExist:
                qs = qs.none()
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")
    estado = request.GET.get("estado")
    if desde:
        try:
            d = datetime.strptime(desde, "%Y-%m-%d").date()
            qs = qs.filter(fecha_hora__date__gte=d)
        except ValueError:
            pass
    if hasta:
        try:
            h = datetime.strptime(hasta, "%Y-%m-%d").date()
            qs = qs.filter(fecha_hora__date__lte=h)
        except ValueError:
            pass
    if estado:
        qs = qs.filter(estado=estado)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(motivo__icontains=q)
            | Q(paciente__usuario__first_name__icontains=q)
            | Q(paciente__usuario__last_name__icontains=q)
        )
    return qs.order_by("-fecha_hora")


def exportar_citas_pdf(request):
    qs = _filtro_citas(request)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, title="Reporte de citas")
    data = [["ID", "Paciente", "Médico", "Fecha", "Estado", "Motivo"]]
    for c in qs[:500]:
        data.append(
            [
                str(c.pk),
                str(c.paciente),
                str(c.medico),
                dj_tz.localtime(c.fecha_hora).strftime("%Y-%m-%d %H:%M"),
                c.get_estado_display(),
                (c.motivo or "")[:60],
            ]
        )
    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E1F53")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
            ]
        )
    )
    doc.build([t])
    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'attachment; filename="citas_reporte.pdf"'
    return resp


def exportar_citas_excel(request):
    qs = _filtro_citas(request)
    wb = Workbook()
    ws = wb.active
    ws.title = "Citas"
    ws.append(["ID", "Paciente", "Médico", "Fecha y hora", "Estado", "Motivo"])
    for c in qs[:2000]:
        ws.append(
            [
                c.pk,
                str(c.paciente),
                str(c.medico),
                dj_tz.localtime(c.fecha_hora).strftime("%Y-%m-%d %H:%M"),
                c.get_estado_display(),
                c.motivo,
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    data = buf.getvalue()
    buf.close()
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = 'attachment; filename="citas_reporte.xlsx"'
    return resp
