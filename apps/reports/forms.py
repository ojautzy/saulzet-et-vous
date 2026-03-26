"""Forms for the reports app."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Report

MAX_PHOTOS = 5
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}


class ReportForm(forms.ModelForm):
    """Form for creating a new report (sollicitation)."""

    class Meta:
        model = Report
        fields = ["report_type", "title", "description", "latitude", "longitude", "location_text", "is_public"]
        widgets = {
            "report_type": forms.RadioSelect,
            "title": forms.TextInput(
                attrs={
                    "placeholder": _("Titre de votre sollicitation"),
                    "class": "input input-bordered w-full font-sans",
                    "maxlength": 200,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": _("Décrivez votre question, idée ou signalement..."),
                    "class": "textarea textarea-bordered w-full font-serif min-h-[150px]",
                    "rows": 6,
                }
            ),
            "latitude": forms.HiddenInput,
            "longitude": forms.HiddenInput,
            "location_text": forms.TextInput(
                attrs={
                    "placeholder": _("Ex : Devant la mairie, Chemin de..."),
                    "class": "input input-bordered w-full font-sans",
                }
            ),
            "is_public": forms.CheckboxInput(
                attrs={
                    "class": "checkbox checkbox-success",
                }
            ),
        }
        labels = {
            "is_public": _("Rendre ma sollicitation publique"),
        }

    def clean(self) -> dict:
        """Validate uploaded photos from request files."""
        cleaned_data = super().clean()
        files = self.files.getlist("photos")
        if len(files) > MAX_PHOTOS:
            raise ValidationError(
                _("Vous ne pouvez pas envoyer plus de %(max)s photos."),
                params={"max": MAX_PHOTOS},
            )
        for f in files:
            if f.size > MAX_PHOTO_SIZE:
                raise ValidationError(
                    _("Le fichier %(name)s dépasse la taille maximale de 10 Mo."),
                    params={"name": f.name},
                )
            ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
            if f".{ext}" not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    _("Le format du fichier %(name)s n'est pas accepté."),
                    params={"name": f.name},
                )
        return cleaned_data


class ReportEditForm(forms.ModelForm):
    """Form for editing an existing report (limited fields)."""

    class Meta:
        model = Report
        fields = ["latitude", "longitude", "location_text", "is_public"]
        widgets = {
            "latitude": forms.HiddenInput,
            "longitude": forms.HiddenInput,
            "location_text": forms.TextInput(
                attrs={
                    "placeholder": _("Ex : Devant la mairie, Chemin de..."),
                    "class": "input input-bordered w-full font-sans",
                }
            ),
            "is_public": forms.CheckboxInput(
                attrs={
                    "class": "checkbox checkbox-success",
                }
            ),
        }
        labels = {
            "is_public": _("Sollicitation publique"),
        }
