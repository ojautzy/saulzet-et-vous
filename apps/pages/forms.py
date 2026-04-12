"""Forms for pages app."""

import time

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Minimum time (seconds) a human needs to fill the form.
CONTACT_MIN_SUBMIT_SECONDS = 3


class ContactForm(forms.Form):
    name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": _("Votre nom"),
        }),
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": _("votre@email.fr"),
        }),
    )
    subject = forms.CharField(
        label=_("Objet"),
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": _("Objet de votre message"),
        }),
    )
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={
            "class": "textarea textarea-bordered w-full",
            "rows": 6,
            "placeholder": _("Votre message..."),
        }),
    )

    # --- Anti-spam fields ---

    # Honeypot: invisible to humans, bots fill it automatically.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "tabindex": "-1",
            "autocomplete": "off",
        }),
    )

    # Timestamp: set by the view on GET, checked on POST.
    timestamp = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )

    def clean_website(self):
        """Reject submission if the honeypot field is filled."""
        value = self.cleaned_data.get("website", "")
        if value:
            raise ValidationError("")
        return value

    def clean_timestamp(self):
        """Reject submission if it arrives faster than a human can type."""
        raw = self.cleaned_data.get("timestamp", "")
        if not raw:
            raise ValidationError("")
        try:
            ts = float(raw)
        except (ValueError, TypeError):
            raise ValidationError("")
        elapsed = time.time() - ts
        if elapsed < CONTACT_MIN_SUBMIT_SECONDS:
            raise ValidationError("")
        return raw
