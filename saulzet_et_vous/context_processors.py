"""Custom context processors for Saulzet & Vous."""

from pathlib import Path

from django.conf import settings


def version(request):
    """Inject the project version from the VERSION file into all templates."""
    version_file = Path(settings.BASE_DIR) / "VERSION"
    try:
        project_version = version_file.read_text().strip()
    except FileNotFoundError:
        project_version = "dev"
    return {"PROJECT_VERSION": project_version}
