from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Debe indicarse un correo electrónico.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario con rol: administrador, operador (recepción), médico o paciente."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        OPERADOR = "OPERADOR", "Operador (atención)"
        MEDICO = "MEDICO", "Médico"
        PACIENTE = "PACIENTE", "Paciente"

    username = models.CharField("nombre de usuario", max_length=150, unique=True, blank=True)
    email = models.EmailField("correo electrónico", unique=True)
    role = models.CharField(
        "rol",
        max_length=20,
        choices=Role.choices,
        default=Role.PACIENTE,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_role_display()})"
