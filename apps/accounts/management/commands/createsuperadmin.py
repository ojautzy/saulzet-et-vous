"""Management command to create a super admin user."""

import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """Create a superuser with role=admin and is_approved=True."""

    help = "Create a super admin user (role=admin, is_approved=True, is_staff=True, is_superuser=True)"

    def handle(self, *args, **options) -> None:
        self.stdout.write("Création d'un super-administrateur Saulzet & Vous\n")

        email = input("Email : ").strip()
        if not email:
            raise CommandError("L'email est obligatoire.")

        if User.objects.filter(email=email).exists():
            raise CommandError(f"Un utilisateur avec l'email '{email}' existe déjà.")

        first_name = input("Prénom : ").strip()
        last_name = input("Nom : ").strip()

        password = getpass.getpass("Mot de passe : ")
        password_confirm = getpass.getpass("Confirmer le mot de passe : ")

        if password != password_confirm:
            raise CommandError("Les mots de passe ne correspondent pas.")

        if not password:
            raise CommandError("Le mot de passe est obligatoire.")

        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Super-administrateur '{user.email}' créé avec succès.")
        )
