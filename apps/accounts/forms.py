"""Forms for accounts app."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
)
from django.contrib.auth.forms import (
    PasswordChangeForm as DjangoPasswordChangeForm,
)
from django.contrib.auth.forms import (
    SetPasswordForm as DjangoSetPasswordForm,
)
from django.utils.translation import gettext_lazy as _

PASSWORD_INPUT_CLASS = "input input-bordered w-full"

User = get_user_model()


class MagicLinkForm(forms.Form):
    """Form to request a magic link login."""

    email = forms.EmailField(
        label=_("Adresse email"),
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": _("votre@email.fr"),
                "autocomplete": "email",
            }
        ),
    )


class LoginForm(AuthenticationForm):
    """Form for password-based login."""

    username = forms.EmailField(
        label=_("Adresse email"),
        widget=forms.EmailInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": _("votre@email.fr"),
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": _("Votre mot de passe"),
                "autocomplete": "current-password",
            }
        ),
    )


class RegisterForm(forms.ModelForm):
    """Form for user registration."""

    password1 = forms.CharField(
        label=_("Mot de passe (optionnel)"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": _("Laissez vide pour utiliser le magic link"),
                "autocomplete": "new-password",
            }
        ),
        help_text=_("Si non renseigné, seul le magic link sera utilisable pour vous connecter."),
    )
    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": _("Confirmez votre mot de passe"),
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "address", "village")
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": _("votre@email.fr"),
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": _("Prénom"),
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": _("Nom"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": _("06 12 34 56 78"),
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "input input-bordered w-full",
                    "placeholder": _("Ex : 3 rue du Bourg"),
                }
            ),
            "village": forms.Select(
                attrs={
                    "class": "select select-bordered w-full",
                }
            ),
        }
        labels = {
            "email": _("Adresse email"),
            "first_name": _("Prénom"),
            "last_name": _("Nom"),
            "phone": _("Téléphone"),
            "address": _("Adresse à Saulzet-le-Froid"),
            "village": _("Village / Hameau"),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["phone"].required = True
        self.fields["address"].required = True
        self.fields["village"].required = True

    def clean(self) -> dict:
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password1 != password2:
            self.add_error("password2", _("Les mots de passe ne correspondent pas."))
        return cleaned_data

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.is_approved = False
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Form for editing user profile."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "address", "village")
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "address": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "village": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
        }
        labels = {
            "first_name": _("Prénom"),
            "last_name": _("Nom"),
            "phone": _("Téléphone"),
            "address": _("Adresse à Saulzet-le-Froid"),
            "village": _("Village / Hameau"),
        }


def _style_password_fields(form: forms.Form) -> None:
    """Apply the DaisyUI input class to all password fields of a form."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", PASSWORD_INPUT_CLASS)
        field.widget.attrs.setdefault("autocomplete", "new-password")


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Password change form for users that already have a usable password."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _style_password_fields(self)
        self.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["old_password"].label = _("Mot de passe actuel")
        self.fields["new_password1"].label = _("Nouveau mot de passe")
        self.fields["new_password2"].label = _("Confirmer le nouveau mot de passe")


class PasswordSetForm(DjangoSetPasswordForm):
    """Password set form for users without a usable password (magic link only)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        _style_password_fields(self)
        self.fields["new_password1"].label = _("Mot de passe")
        self.fields["new_password2"].label = _("Confirmer le mot de passe")
