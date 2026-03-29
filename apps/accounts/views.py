"""Views for accounts app."""

import hashlib
import secrets
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .forms import LoginForm, MagicLinkForm, ProfileForm, RegisterForm

User = get_user_model()


def home_view(request: HttpRequest) -> HttpResponse:
    """Render the home page."""
    return render(request, "home.html")


def login_view(request: HttpRequest) -> HttpResponse:
    """Render the login page with magic link and password tabs."""
    if request.user.is_authenticated:
        return redirect("home")

    magic_form = MagicLinkForm()
    password_form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {"magic_form": magic_form, "password_form": password_form},
    )


def magic_link_request_view(request: HttpRequest) -> HttpResponse:
    """Handle magic link request."""
    if request.method != "POST":
        return redirect("accounts:login")

    form = MagicLinkForm(request.POST)
    if not form.is_valid():
        password_form = LoginForm()
        return render(
            request,
            "accounts/login.html",
            {"magic_form": form, "password_form": password_form, "active_tab": "magic"},
        )

    email = form.cleaned_data["email"]
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists — show success message anyway
        messages.success(
            request,
            _("Si un compte existe avec cette adresse, un lien de connexion a été envoyé."),
        )
        return redirect("accounts:login")

    if not user.is_approved:
        messages.warning(
            request,
            _("Votre compte est en attente de validation par un administrateur."),
        )
        return redirect("accounts:pending")

    # Generate token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    user.magic_link_token = token_hash
    user.magic_link_expires = timezone.now() + timezone.timedelta(
        minutes=settings.MAGIC_LINK_EXPIRY_MINUTES
    )
    user.save(update_fields=["magic_link_token", "magic_link_expires"])

    # Build magic link URL
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    magic_url = f"{site_url}/accounts/magic/{raw_token}/"

    # Send email
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    send_mail(
        subject=_("Votre lien de connexion — Saulzet & Vous"),
        message=render_to_string(
            "accounts/emails/magic_link.txt",
            {"user": user, "magic_url": magic_url, "expiry_minutes": settings.MAGIC_LINK_EXPIRY_MINUTES},
        ),
        from_email=config.from_email,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(
        request,
        _("Si un compte existe avec cette adresse, un lien de connexion a été envoyé."),
    )
    return redirect("accounts:login")


def magic_link_verify_view(request: HttpRequest, token: str) -> HttpResponse:
    """Verify a magic link token and log the user in."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    try:
        user = User.objects.get(magic_link_token=token_hash)
    except User.DoesNotExist:
        messages.error(request, _("Ce lien de connexion est invalide ou a déjà été utilisé."))
        return redirect("accounts:login")

    # Check expiry
    if user.magic_link_expires and user.magic_link_expires < timezone.now():
        user.magic_link_token = None
        user.magic_link_expires = None
        user.save(update_fields=["magic_link_token", "magic_link_expires"])
        messages.error(request, _("Ce lien de connexion a expiré. Veuillez en demander un nouveau."))
        return redirect("accounts:login")

    # Check approval
    if not user.is_approved:
        user.magic_link_token = None
        user.magic_link_expires = None
        user.save(update_fields=["magic_link_token", "magic_link_expires"])
        messages.warning(request, _("Votre compte est en attente de validation par un administrateur."))
        return redirect("accounts:pending")

    # Invalidate token (one-time use)
    user.magic_link_token = None
    user.magic_link_expires = None
    user.save(update_fields=["magic_link_token", "magic_link_expires"])

    # Log the user in
    login(request, user)
    messages.success(request, _("Bienvenue, %(name)s !") % {"name": user.first_name})
    return redirect("home")


class PasswordLoginView(LoginView):
    """Handle password-based login."""

    form_class = LoginForm
    template_name = "accounts/login.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["magic_form"] = MagicLinkForm()
        context["password_form"] = context.pop("form")
        context["active_tab"] = "password"
        return context

    def form_valid(self, form: LoginForm) -> HttpResponse:
        user = form.get_user()
        if not user.is_approved:
            messages.warning(
                self.request,
                _("Votre compte est en attente de validation par un administrateur."),
            )
            return redirect("accounts:pending")
        messages.success(
            self.request,
            _("Bienvenue, %(name)s !") % {"name": user.first_name},
        )
        return super().form_valid(form)


def register_view(request: HttpRequest) -> HttpResponse:
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Notify admins/mayor via notification service
            from apps.notifications.services import notify_new_registration

            notify_new_registration(user)

            messages.success(
                request,
                _("Votre inscription a bien été enregistrée. "
                  "Elle sera validée par un administrateur dans les plus brefs délais."),
            )
            return redirect("accounts:pending")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def pending_view(request: HttpRequest) -> HttpResponse:
    """Show the pending approval page."""
    return render(request, "accounts/pending.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the user out."""
    logout(request)
    messages.info(request, _("Vous avez été déconnecté(e)."))
    return redirect("home")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Display and edit user profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Votre profil a été mis à jour."))
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
def delete_account_view(request: HttpRequest) -> HttpResponse:
    """Delete the current user's account."""
    if request.method != "POST":
        return redirect("accounts:profile")

    user = request.user
    logout(request)
    user.delete()
    messages.info(request, _("Votre compte a été supprimé. Nous espérons vous revoir bientôt."))
    return redirect("home")
