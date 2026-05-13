from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

# Modelos de dominio: especialidad, médico, paciente, cita, disponibilidad e historia clínica.


class Specialty(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "especialidad"
        verbose_name_plural = "especialidades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Doctor(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_medico",
    )
    especialidad = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="medicos",
    )
    cedula_profesional = models.CharField(max_length=50, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    biografia = models.TextField(blank=True)

    class Meta:
        verbose_name = "médico"
        verbose_name_plural = "médicos"
        ordering = ["usuario__last_name", "usuario__first_name"]

    def __str__(self):
        return self.usuario.get_full_name() or str(self.usuario)


class Patient(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_paciente",
    )
    fecha_nacimiento = models.DateField()
    tipo_sangre = models.CharField(max_length=5, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    contacto_emergencia = models.CharField(max_length=120, blank=True)
    numero_seguro = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["usuario__last_name"]

    def __str__(self):
        return self.usuario.get_full_name() or str(self.usuario)


class DoctorAvailability(models.Model):
    """Franja recurrente de disponibilidad del médico (por día de la semana)."""

    class DiaSemana(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    medico = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    dia_semana = models.PositiveSmallIntegerField(choices=DiaSemana.choices)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        verbose_name = "horario disponible"
        verbose_name_plural = "horarios disponibles"
        ordering = ["medico", "dia_semana", "hora_inicio"]
        constraints = [
            models.UniqueConstraint(
                fields=["medico", "dia_semana", "hora_inicio", "hora_fin"],
                name="uniq_medico_dia_franja",
            ),
        ]

    def clean(self):
        if self.hora_inicio and self.hora_fin and self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser menor que la hora de fin.")

    def __str__(self):
        return f"{self.medico} — {self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}"


class Appointment(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = "PROGRAMADA", "Programada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"

    paciente = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="citas",
    )
    medico = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="citas",
    )
    fecha_hora = models.DateTimeField()
    duracion_minutos = models.PositiveSmallIntegerField(default=30)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADA,
    )
    motivo = models.CharField(max_length=255)
    notas = models.TextField(blank=True)
    certificado = models.FileField(
        "certificado digital",
        upload_to="certificados_cita/%Y/%m/",
        blank=True,
        null=True,
        help_text="PDF o imagen asociada a la cita (paciente).",
    )
    certificado_notas = models.TextField(
        "notas del certificado",
        blank=True,
        help_text="Datos adicionales que deben figurar con el certificado.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "cita"
        verbose_name_plural = "citas"
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["medico", "fecha_hora"]),
            models.Index(fields=["paciente", "fecha_hora"]),
        ]

    def clean(self):
        from datetime import timedelta

        if not self.medico_id or not self.fecha_hora:
            return
        dur = self.duracion_minutos or 30
        fin_self = self.fecha_hora + timedelta(minutes=dur)
        qs = Appointment.objects.filter(medico_id=self.medico_id).filter(
            estado__in=[self.Estado.PROGRAMADA, self.Estado.CONFIRMADA]
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        for otra in qs:
            otra_fin = otra.fecha_hora + timedelta(
                minutes=otra.duracion_minutos or 30
            )
            if self.fecha_hora < otra_fin and fin_self > otra.fecha_hora:
                raise ValidationError(
                    "El médico ya tiene una cita activa en ese horario."
                )

    def __str__(self):
        return f"{self.paciente} / {self.medico} @ {self.fecha_hora}"


class MedicalRecord(models.Model):
    paciente = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="historias",
    )
    medico = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="historias",
    )
    cita = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historias",
    )
    fecha_consulta = models.DateField()
    diagnostico = models.TextField()
    receta = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "historia clínica"
        verbose_name_plural = "historias clínicas"
        ordering = ["-fecha_consulta", "-pk"]

    def __str__(self):
        return f"{self.paciente} — {self.fecha_consulta}"
