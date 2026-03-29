"""Forms for the notifications app."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = (
            "email_status_change",
            "email_new_comment",
            "email_assignment",
            "email_new_report",
            "email_reminder",
        )
        labels = {
            "email_status_change": _("Changement de statut de mes sollicitations"),
            "email_new_comment": _("Nouveau commentaire sur mes sollicitations"),
            "email_assignment": _("Affectation d'une sollicitation (élus)"),
            "email_new_report": _("Nouvelle sollicitation reçue (élus/maire)"),
            "email_reminder": _("Relances automatiques (maire)"),
        }
        widgets = {
            "email_status_change": forms.CheckboxInput(attrs={"class": "checkbox checkbox-sm checkbox-success"}),
            "email_new_comment": forms.CheckboxInput(attrs={"class": "checkbox checkbox-sm checkbox-success"}),
            "email_assignment": forms.CheckboxInput(attrs={"class": "checkbox checkbox-sm checkbox-success"}),
            "email_new_report": forms.CheckboxInput(attrs={"class": "checkbox checkbox-sm checkbox-success"}),
            "email_reminder": forms.CheckboxInput(attrs={"class": "checkbox checkbox-sm checkbox-success"}),
        }
