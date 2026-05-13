"""Señales: correo al confirmar citas."""
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment


@receiver(pre_save, sender=Appointment)
def appointment_guardar_estado_previo(sender, instance, **kwargs):
    if instance.pk:
        try:
            prev = Appointment.objects.only("estado").get(pk=instance.pk)
            instance._estado_anterior = prev.estado
        except Appointment.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Appointment)
def enviar_correo_cita_confirmada(sender, instance, **kwargs):
    if instance.estado != Appointment.Estado.CONFIRMADA:
        return
    anterior = getattr(instance, "_estado_anterior", None)
    if anterior == Appointment.Estado.CONFIRMADA:
        return

    paciente_email = instance.paciente.usuario.email
    medico_email = instance.medico.usuario.email
    subject = "ConsultaMed — Cita confirmada"
    body = (
        f"Su cita ha sido confirmada.\n\n"
        f"Médico: {instance.medico}\n"
        f"Fecha y hora: {instance.fecha_hora}\n"
        f"Motivo: {instance.motivo}\n"
    )
    recipients = [paciente_email]
    if medico_email != paciente_email:
        recipients.append(medico_email)
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )
