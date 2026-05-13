"""Datos de demostración para ConsultaMed (desde cero)."""
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_tz

from consultas.models import (
    Appointment,
    Doctor,
    DoctorAvailability,
    MedicalRecord,
    Patient,
    Specialty,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Crea especialidades, usuarios de prueba, citas y horarios."

    def handle(self, *args, **options):
        if Specialty.objects.exists():
            self.stdout.write(self.style.WARNING("Ya hay datos. Omitiendo seed (borre la BD para re-ejecutar)."))
            return

        esp_card = Specialty.objects.create(
            nombre="Cardiología",
            descripcion="Corazón y sistema circulatorio.",
        )
        esp_med = Specialty.objects.create(
            nombre="Medicina general",
            descripcion="Atención primaria.",
        )

        _unused = User.objects.create_user(
            email="admin@consultamed.local",
            password="Admin123!",
            first_name="Ada",
            last_name="Administrador",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        User.objects.create_user(
            email="operador@consultamed.local",
            password="Operador123!",
            first_name="Oscar",
            last_name="Recepción",
            role=User.Role.OPERADOR,
        )

        doc_user = User.objects.create_user(
            email="medico@consultamed.local",
            password="Medico123!",
            first_name="María",
            last_name="Médico",
            role=User.Role.MEDICO,
        )
        doc = Doctor.objects.create(
            usuario=doc_user,
            especialidad=esp_card,
            cedula_profesional="CED-10001",
            telefono="5550100",
            biografia="Cardióloga.",
        )

        for wd in range(0, 5):
            DoctorAvailability.objects.create(
                medico=doc,
                dia_semana=wd,
                hora_inicio=time(9, 0),
                hora_fin=time(17, 0),
            )

        pac_user = User.objects.create_user(
            email="paciente@consultamed.local",
            password="Paciente123!",
            first_name="Pedro",
            last_name="Paciente",
            role=User.Role.PACIENTE,
        )
        pac = Patient.objects.create(
            usuario=pac_user,
            fecha_nacimiento=date(1990, 5, 15),
            tipo_sangre="O+",
            telefono="5550200",
            contacto_emergencia="Ana Paciente",
            numero_seguro="SGM-998877",
        )

        inicio = dj_tz.make_aware(datetime.combine(date.today() + timedelta(days=1), time(10, 0)))
        c1 = Appointment.objects.create(
            paciente=pac,
            medico=doc,
            fecha_hora=inicio,
            estado=Appointment.Estado.CONFIRMADA,
            motivo="Chequeo general",
            notas="",
        )
        Appointment.objects.create(
            paciente=pac,
            medico=doc,
            fecha_hora=inicio + timedelta(days=2, hours=2),
            estado=Appointment.Estado.PROGRAMADA,
            motivo="Seguimiento",
            notas="",
        )

        MedicalRecord.objects.create(
            paciente=pac,
            medico=doc,
            cita=c1,
            fecha_consulta=date.today(),
            diagnostico="Paciente estable. Continuar observación.",
            receta="Paracetamol 500 mg si dolor.",
            observaciones="",
        )

        self.stdout.write(self.style.SUCCESS("Seed completado. Ver CREDENCIALES_PRUEBA.txt"))
