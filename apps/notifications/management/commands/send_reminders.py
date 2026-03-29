"""Management command to send reminders for orphan reports."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.reports.models import Report
from apps.settings_app.models import SiteSettings

User = get_user_model()


class Command(BaseCommand):
    help = "Envoie des relances pour les sollicitations orphelines (NEW depuis trop longtemps)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Seuil en jours (surcharge la valeur de SiteSettings).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Afficher les relances sans les envoyer.",
        )

    def handle(self, *args, **options):
        config = SiteSettings.load()
        days = options["days"] or config.orphan_days
        dry_run = options["dry_run"]
        interval_days = config.reminder_interval_days

        threshold = timezone.now() - timedelta(days=days)
        orphan_reports = Report.objects.filter(
            status=Report.Status.NEW,
            created_at__lt=threshold,
        ).select_related("author")

        recipients = User.objects.filter(
            role__in=[User.Role.MAYOR, User.Role.ELECTED],
            is_approved=True,
        )

        reminder_count = 0

        for report in orphan_reports:
            # Check if a reminder was already sent recently
            recent_reminder = Notification.objects.filter(
                report=report,
                notification_type=Notification.Type.REMINDER,
                created_at__gte=timezone.now() - timedelta(days=interval_days),
            ).exists()

            if recent_reminder:
                continue

            days_since = (timezone.now() - report.created_at).days

            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Relance pour « {report.title} » "
                    f"({days_since} jours) — {recipients.count()} destinataires"
                )
                reminder_count += 1
                continue

            for recipient in recipients:
                notify(
                    recipient=recipient,
                    notification_type=Notification.Type.REMINDER,
                    title=f"Relance : {report.title}",
                    message=f"La sollicitation « {report.title} » attend une prise en charge depuis {days_since} jours.",
                    url=f"/etvous/tableau-de-bord/{report.pk}/",
                    report=report,
                    email_subject=f"Relance — {report.title}",
                    email_template="reminder",
                    email_context={
                        "report": report,
                        "days_since_creation": days_since,
                    },
                )
            reminder_count += 1

        action = "identifiée(s)" if dry_run else "envoyée(s)"
        self.stdout.write(
            self.style.SUCCESS(f"{reminder_count} relance(s) {action}.")
        )
