"""
URL configuration for hospital_gestion project.
"""
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("accounts.urls")),
    path("", include("consultas.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=Path(settings.BASE_DIR) / "static",
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
