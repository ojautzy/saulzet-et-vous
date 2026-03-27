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
        SECRETARY = "secretary", _("Secrétaire de mairie")
        MAYOR = "mayor", _("Maire / 1er Adjoint")
        ELECTED = "elected", _("Adjoint / Conseiller")
        CITIZEN = "citizen", _("Habitant")

    class Village(models.TextChoices):
        BOURG = "bourg", _("Le Bourg")
        SOUVERAND = "souverand", _("Souverand")
        ZANIERES = "zanieres", _("Zanières")
        PESSADE = "pessade", _("Pessade")
        LA_MARTRE = "la_martre", _("La Martre")
        ESPINASSE = "espinasse", _("Espinasse")

    # Remove username field, use email instead
    username = None
    email = models.EmailField(_("adresse email"), unique=True)

    role = models.CharField(
        _("rôle"),
        max_length=10,
        choices=Role.choices,
        default=Role.CITIZEN,
    )
    photo = models.ImageField(
        _("photo"),
        upload_to="accounts/photos/",
        blank=True,
        null=True,
        help_text=_("Photo pour la page équipe municipale."),
    )
    function_title = models.CharField(
        _("fonction"),
        max_length=100,
        blank=True,
        help_text=_("Ex: Maire, 1er Adjoint, Conseiller municipal"),
    )
    function_order = models.PositiveIntegerField(
        _("ordre d'affichage"),
        default=100,
        help_text=_("Ordre sur la page équipe (1 = Maire, 2 = 1er Adjoint, etc.)"),
    )
    is_approved = models.BooleanField(
        _("compte approuvé"),
        default=False,
        help_text=_("Indique si le compte a été validé par un administrateur."),
    )
    phone = models.CharField(_("téléphone"), max_length=20, blank=True)
    address = models.CharField(_("adresse à Saulzet-le-Froid"), max_length=255, blank=True)
    village = models.CharField(
        _("village"),
        max_length=20,
        choices=Village.choices,
        blank=True,
        help_text=_("Village ou hameau de résidence à Saulzet-le-Froid."),
    )
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
    def is_secretary(self) -> bool:
        return self.role == self.Role.SECRETARY

    @property
    def is_mayor(self) -> bool:
        return self.role == self.Role.MAYOR

    @property
    def is_elected(self) -> bool:
        return self.role in (self.Role.MAYOR, self.Role.ELECTED)

    @property
    def is_staff_member(self) -> bool:
        return self.role in (
            self.Role.ADMIN,
            self.Role.SECRETARY,
            self.Role.MAYOR,
            self.Role.ELECTED,
        )
