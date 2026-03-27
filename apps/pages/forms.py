"""Forms for pages app."""

from django import forms
from django.utils.translation import gettext_lazy as _


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
