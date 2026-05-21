"""
URL configuration for hospital_gestion project.
"""
import os
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.static import serve


def health(_request):
    """Health check para Render / balanceadores."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("health/", health, name="health"),
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
elif os.environ.get("SERVE_MEDIA", "True").lower() in ("1", "true", "yes"):
    # Certificados adjuntos por pacientes (disco persistente en Render).
    urlpatterns += [
        path(
            "media/<path:path>",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
