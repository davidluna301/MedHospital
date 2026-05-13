"""Constancia PDF de una cita (solo datos del sistema)."""
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone as dj_tz
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def constancia_cita_pdf_response(cita):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        title=f"Constancia cita {cita.pk}",
        rightMargin=72,
        leftMargin=72,
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("<b>ConsultaMed — Constancia de cita</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    fh = dj_tz.localtime(cita.fecha_hora).strftime("%Y-%m-%d %H:%M")
    data = [
        ["Número de cita", str(cita.pk)],
        ["Paciente", str(cita.paciente)],
        ["Correo paciente", cita.paciente.usuario.email],
        ["Médico", str(cita.medico)],
        ["Especialidad", str(cita.medico.especialidad)],
        ["Fecha y hora", fh],
        ["Duración (min)", str(cita.duracion_minutos)],
        ["Estado", cita.get_estado_display()],
        ["Motivo", cita.motivo or "—"],
    ]
    if cita.notas:
        data.append(["Notas internas", cita.notas[:500]])
    if cita.certificado_notas:
        data.append(["Notas del certificado", cita.certificado_notas[:500]])
    t = Table(data, colWidths=[140, 340])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0E1F53")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            "<i>Este documento resume la información registrada en el sistema. "
            "No sustituye una receta médica firmada.</i>",
            styles["Normal"],
        )
    )
    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="constancia_cita_{cita.pk}.pdf"'
    return resp
