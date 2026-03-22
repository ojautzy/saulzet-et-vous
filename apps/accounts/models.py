"""User model and manager for accounts app."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager that uses email as the unique identifier."""

    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        """Create and return a regular user with the given email."""
        if not email:
            raise ValueError(_("L'adresse email est obligatoire."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields
    ) -> "User":
        """Create and return a superuser with the given email."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approved", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Le superutilisateur doit avoir is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Le superutilisateur doit avoir is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Extended user model with roles and magic link support."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Administrateur")
        MAYOR = "mayor", _("Maire / 1er Adjoint")
        ELECTED = "elected", _("Adjoint / Conseiller")
        CITIZEN = "citizen", _("Habitant")

    # Remove username field, use email instead
    username = None
    email = models.EmailField(_("adresse email"), unique=True)

    role = models.CharField(
        _("rôle"),
        max_length=10,
        choices=Role.choices,
        default=Role.CITIZEN,
    )
    is_approved = models.BooleanField(
        _("compte approuvé"),
        default=False,
        help_text=_("Indique si le compte a été validé par un administrateur."),
    )
    phone = models.CharField(_("téléphone"), max_length=20, blank=True)
    address = models.CharField(_("adresse à Saulzet-le-Froid"), max_length=255, blank=True)
    magic_link_token = models.CharField(max_length=64, null=True, blank=True)
    magic_link_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(_("date de création"), auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.get_full_name() or self.email

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_mayor(self) -> bool:
        return self.role == self.Role.MAYOR

    @property
    def is_elected(self) -> bool:
        return self.role in (self.Role.MAYOR, self.Role.ELECTED)
