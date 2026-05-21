"""Datos de demostración ampliados para ConsultaMed (gráficos y listados)."""
import os
import random
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

# Contraseña común para cuentas generadas (además de las 4 principales en CREDENCIALES_PRUEBA.txt).
DEMO_PASSWORD = "Demo123!"

SPECIALTIES = [
    ("Cardiología", "Corazón y sistema circulatorio."),
    ("Medicina general", "Atención primaria y chequeos."),
    ("Pediatría", "Atención infantil y adolescentes."),
    ("Traumatología", "Lesiones óseas y musculares."),
    ("Ginecología", "Salud reproductiva femenina."),
    ("Dermatología", "Piel, cabello y uñas."),
    ("Neurología", "Sistema nervioso central y periférico."),
    ("Oftalmología", "Salud visual y cirugía ocular."),
]

# (nombre, apellido, email, especialidad_nombre, cédula)
DOCTORS = [
    ("María", "Médico", "medico@consultamed.local", "Cardiología", "CED-10001"),
    ("Carlos", "Ramírez", "medico02@consultamed.local", "Cardiología", "CED-10002"),
    ("Laura", "Vega", "medico03@consultamed.local", "Cardiología", "CED-10003"),
    ("Andrés", "Pérez", "medico04@consultamed.local", "Medicina general", "CED-10004"),
    ("Sofía", "López", "medico05@consultamed.local", "Medicina general", "CED-10005"),
    ("Diego", "Castro", "medico06@consultamed.local", "Medicina general", "CED-10006"),
    ("Elena", "Morales", "medico07@consultamed.local", "Pediatría", "CED-10007"),
    ("Jorge", "Herrera", "medico08@consultamed.local", "Pediatría", "CED-10008"),
    ("Patricia", "Núñez", "medico09@consultamed.local", "Traumatología", "CED-10009"),
    ("Ricardo", "Silva", "medico10@consultamed.local", "Traumatología", "CED-10010"),
    ("Camila", "Rojas", "medico11@consultamed.local", "Ginecología", "CED-10011"),
    ("Felipe", "Torres", "medico12@consultamed.local", "Dermatología", "CED-10012"),
    ("Valentina", "Mesa", "medico13@consultamed.local", "Neurología", "CED-10013"),
    ("Tomás", "Aguilar", "medico14@consultamed.local", "Oftalmología", "CED-10014"),
]

PATIENT_FIRST_NAMES = [
    "Pedro", "Ana", "Luis", "Carmen", "Miguel", "Rosa", "Javier", "Lucía",
    "Fernando", "Isabel", "Roberto", "Marta", "Daniel", "Paula", "Sergio",
    "Elena", "Alberto", "Clara", "Raúl", "Teresa", "Óscar", "Beatriz", "Iván",
    "Nuria", "Héctor", "Silvia", "Rubén", "Pilar", "Gonzalo", "Cristina",
    "Marcos", "Adriana", "Víctor", "Inés", "Emilio", "Rocío", "Arturo",
    "Mercedes", "Enrique", "Dolores", "Ramón", "Concepción", "Alfredo",
    "Esperanza", "Joaquín", "Amparo", "Felipe", "Remedios", "Ignacio", "Soledad",
]

PATIENT_LAST_NAMES = [
    "García", "Martínez", "López", "Sánchez", "González", "Rodríguez", "Fernández",
    "Pérez", "Gómez", "Ruiz", "Díaz", "Moreno", "Álvarez", "Romero", "Navarro",
    "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco",
    "Molina", "Suárez", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín",
    "Iglesias", "Medina", "Garrido", "Cortés", "Castillo", "Santos", "Lozano",
    "Guerrero", "Cano", "Prieto", "Méndez", "Cruz", "Calvo", "Gallego", "Vidal",
    "León", "Herrera", "Márquez", "Peña", "Flores", "Cabrera", "Campos", "Vega",
]

MOTIVOS = [
    "Chequeo general",
    "Control de rutina",
    "Seguimiento postoperatorio",
    "Dolor abdominal",
    "Cefalea recurrente",
    "Control de presión",
    "Revisión de estudios",
    "Consulta de seguimiento",
    "Evaluación inicial",
    "Renovación de receta",
    "Control pediátrico",
    "Dolor articular",
]

# Pesos por especialidad para citas (más barras visibles en el gráfico).
CITAS_POR_ESPECIALIDAD = {
    "Cardiología": 42,
    "Medicina general": 38,
    "Pediatría": 28,
    "Traumatología": 26,
    "Ginecología": 22,
    "Dermatología": 20,
    "Neurología": 18,
    "Oftalmología": 16,
}


class Command(BaseCommand):
    help = "Crea especialidades, personal, pacientes y citas de demostración (dataset amplio)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Elimina datos de demo existentes y vuelve a cargar el dataset amplio.",
        )

    def _clear_demo_data(self):
        """Borra citas, perfiles y usuarios @consultamed.local (seed anterior o amplio)."""
        self.stdout.write("Eliminando datos de demostración existentes…")
        MedicalRecord.objects.all().delete()
        Appointment.objects.all().delete()
        DoctorAvailability.objects.all().delete()
        Patient.objects.all().delete()
        Doctor.objects.all().delete()
        Specialty.objects.all().delete()
        deleted_users, _ = User.objects.filter(email__iendswith="@consultamed.local").delete()
        self.stdout.write(self.style.WARNING(f"  Usuarios demo eliminados: {deleted_users}"))

    def _needs_dataset_upgrade(self) -> bool:
        """Detecta el seed pequeño antiguo (p. ej. 2 especialidades, pocas citas)."""
        if not Specialty.objects.exists():
            return False
        return (
            Specialty.objects.count() < len(SPECIALTIES)
            or Patient.objects.count() < 40
            or Appointment.objects.count() < 100
        )

    def handle(self, *args, **options):
        force = options["force"] or os.environ.get("SEED_DEMO_FORCE", "").lower() == "true"

        if Specialty.objects.exists():
            if self._needs_dataset_upgrade():
                self.stdout.write(
                    self.style.WARNING(
                        "Seed antiguo detectado (pocos registros). "
                        "Actualizando al dataset amplio…"
                    )
                )
                self._clear_demo_data()
            elif not force:
                self.stdout.write(
                    self.style.WARNING(
                        "Ya hay datos (dataset amplio). Omitiendo seed. "
                        "Use --force o SEED_DEMO_FORCE=true para reemplazar."
                    )
                )
                return
            else:
                self._clear_demo_data()

        self._run_seed()

    def _run_seed(self):
        random.seed(42)
        esp_map = {}
        for nombre, desc in SPECIALTIES:
            esp_map[nombre] = Specialty.objects.create(nombre=nombre, descripcion=desc)

        User.objects.create_user(
            email="admin@consultamed.local",
            password="Admin123!",
            first_name="Ada",
            last_name="Administrador",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        for email, first, last in (
            ("operador@consultamed.local", "Oscar", "Recepción"),
            ("operador02@consultamed.local", "Lucía", "Front desk"),
        ):
            User.objects.create_user(
                email=email,
                password="Operador123!" if email == "operador@consultamed.local" else DEMO_PASSWORD,
                first_name=first,
                last_name=last,
                role=User.Role.OPERADOR,
            )

        doctors = []
        for first, last, email, esp_nombre, cedula in DOCTORS:
            pwd = "Medico123!" if email == "medico@consultamed.local" else DEMO_PASSWORD
            doc_user = User.objects.create_user(
                email=email,
                password=pwd,
                first_name=first,
                last_name=last,
                role=User.Role.MEDICO,
            )
            doc = Doctor.objects.create(
                usuario=doc_user,
                especialidad=esp_map[esp_nombre],
                cedula_profesional=cedula,
                telefono=f"555{cedula[-4:]}",
                biografia=f"Especialista en {esp_nombre}.",
            )
            doctors.append(doc)
            for wd in range(0, 5):
                DoctorAvailability.objects.create(
                    medico=doc,
                    dia_semana=wd,
                    hora_inicio=time(8, 0),
                    hora_fin=time(18, 0),
                )

        doctors_by_esp = {}
        for doc in doctors:
            doctors_by_esp.setdefault(doc.especialidad.nombre, []).append(doc)

        patients = []
        hoy = date.today()
        paciente_main_email = "paciente@consultamed.local"

        for i in range(55):
            fn = PATIENT_FIRST_NAMES[i % len(PATIENT_FIRST_NAMES)]
            ln = PATIENT_LAST_NAMES[i % len(PATIENT_LAST_NAMES)]
            if i == 0:
                email = paciente_main_email
                pwd = "Paciente123!"
            else:
                email = f"paciente{i + 1:02d}@consultamed.local"
                pwd = DEMO_PASSWORD

            pac_user = User.objects.create_user(
                email=email,
                password=pwd,
                first_name=fn,
                last_name=ln,
                role=User.Role.PACIENTE,
            )
            nacimiento = hoy - timedelta(days=365 * (22 + (i % 45)))
            pac = Patient.objects.create(
                usuario=pac_user,
                fecha_nacimiento=nacimiento,
                tipo_sangre=random.choice(["O+", "A+", "B+", "AB+", "O-"]),
                telefono=f"5551{i:04d}",
                contacto_emergencia=f"Contacto {ln}",
                numero_seguro=f"SGM-{100000 + i}",
            )
            patients.append(pac)

            # Distribuir altas en los últimos 12 meses (gráfico pacientes por mes).
            meses_atras = i % 12
            dias_extra = (i * 3) % 25 + 1
            joined_naive = datetime.combine(hoy, time(9, 0)) - timedelta(
                days=30 * meses_atras + dias_extra
            )
            User.objects.filter(pk=pac_user.pk).update(date_joined=dj_tz.make_aware(joined_naive))

        estados_pool = (
            [Appointment.Estado.COMPLETADA] * 50
            + [Appointment.Estado.CONFIRMADA] * 20
            + [Appointment.Estado.PROGRAMADA] * 18
            + [Appointment.Estado.CANCELADA] * 12
        )
        citas_bulk = []
        ahora = dj_tz.now()

        for esp_nombre, cantidad in CITAS_POR_ESPECIALIDAD.items():
            docs_esp = doctors_by_esp[esp_nombre]
            for n in range(cantidad):
                doc = docs_esp[n % len(docs_esp)]
                pac = patients[n % len(patients)]
                dias = random.randint(-150, 45)
                hora = random.choice([8, 9, 10, 11, 14, 15, 16, 17])
                minuto = random.choice([0, 15, 30, 45])
                base = (ahora + timedelta(days=dias)).date()
                fecha = dj_tz.make_aware(datetime.combine(base, time(hora, minuto)))
                estado = random.choice(estados_pool)
                if dias < -7 and estado == Appointment.Estado.PROGRAMADA:
                    estado = random.choice(
                        [
                            Appointment.Estado.COMPLETADA,
                            Appointment.Estado.COMPLETADA,
                            Appointment.Estado.CANCELADA,
                        ]
                    )

                citas_bulk.append(
                    Appointment(
                        paciente=pac,
                        medico=doc,
                        fecha_hora=fecha,
                        estado=estado,
                        motivo=random.choice(MOTIVOS),
                        notas="",
                        duracion_minutos=30,
                    )
                )

        Appointment.objects.bulk_create(citas_bulk, batch_size=200)

        # Historias clínicas para citas completadas (muestra representativa).
        completadas = list(
            Appointment.objects.filter(estado=Appointment.Estado.COMPLETADA).order_by("?")[:45]
        )
        historias = []
        for cita in completadas:
            historias.append(
                MedicalRecord(
                    paciente=cita.paciente,
                    medico=cita.medico,
                    cita=cita,
                    fecha_consulta=cita.fecha_hora.date(),
                    diagnostico=f"Diagnóstico de seguimiento — {cita.motivo[:40]}",
                    receta="Tratamiento según protocolo institucional.",
                    observaciones="Generado por seed_demo.",
                )
            )
        MedicalRecord.objects.bulk_create(historias, batch_size=100)

        total_citas = Appointment.objects.count()
        self.stdout.write(self.style.SUCCESS("Seed completado (dataset amplio)."))
        self.stdout.write(f"  Especialidades: {Specialty.objects.count()}")
        self.stdout.write(f"  Médicos: {Doctor.objects.count()}")
        self.stdout.write(f"  Pacientes: {Patient.objects.count()}")
        self.stdout.write(f"  Citas: {total_citas}")
        self.stdout.write(f"  Historias clínicas: {MedicalRecord.objects.count()}")
        self.stdout.write("  Cuentas principales: CREDENCIALES_PRUEBA.txt")
        self.stdout.write(
            f"  Otras cuentas demo: médicos/pacientes medico02@… paciente02@… contraseña {DEMO_PASSWORD}"
        )
