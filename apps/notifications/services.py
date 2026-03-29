"""Notification service — creates in-app notifications and sends emails."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from .models import Notification, NotificationPreference

User = get_user_model()


def send_notification_email(recipient, subject, template_name, context):
    """Envoie un email HTML + texte avec la charte du site."""
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()

    context["site_settings"] = config
    context["site_url"] = getattr(settings, "SITE_URL", "http://localhost:8000")
    context["recipient"] = recipient

    html_content = render_to_string(f"notifications/emails/{template_name}.html", context)
    text_content = render_to_string(f"notifications/emails/{template_name}.txt", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=config.from_email,
        to=[recipient.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)


def notify(
    recipient,
    notification_type,
    title,
    message,
    url="",
    report=None,
    email_subject=None,
    email_template=None,
    email_context=None,
):
    """Crée une notification in-app et envoie un email si préférences activées."""
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        url=url,
        report=report,
    )

    prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)
    pref_field = f"email_{notification_type}"
    if email_template and hasattr(prefs, pref_field) and getattr(prefs, pref_field):
        send_notification_email(
            recipient, email_subject or title, email_template, email_context or {}
        )

    return notification


def notify_status_change(report, old_status, new_status, changed_by):
    """Notifie l'auteur de la sollicitation d'un changement de statut."""
    if report.author == changed_by:
        return

    from apps.reports.models import Report

    old_label = dict(Report.Status.choices).get(old_status, old_status)
    new_label = dict(Report.Status.choices).get(new_status, new_status)

    notify(
        recipient=report.author,
        notification_type=Notification.Type.STATUS_CHANGE,
        title=_("Changement de statut : %(title)s") % {"title": report.title},
        message=_("Votre sollicitation « %(title)s » est passée de %(old)s à %(new)s.") % {
            "title": report.title,
            "old": old_label,
            "new": new_label,
        },
        url=f"/etvous/{report.pk}/",
        report=report,
        email_subject=_("Changement de statut — %(title)s") % {"title": report.title},
        email_template="status_change",
        email_context={
            "report": report,
            "old_status": old_label,
            "new_status": new_label,
            "changed_by": changed_by,
        },
    )


def notify_new_comment(report, comment, author):
    """Notifie l'auteur (si commentaire d'un élu) ou l'élu assigné (si commentaire de l'auteur)."""
    if author == report.author and report.assigned_to:
        recipient = report.assigned_to
    elif author != report.author:
        recipient = report.author
    else:
        return

    notify(
        recipient=recipient,
        notification_type=Notification.Type.NEW_COMMENT,
        title=_("Nouveau commentaire : %(title)s") % {"title": report.title},
        message=_("%(author)s a commenté votre sollicitation « %(title)s ».") % {
            "author": author.get_full_name(),
            "title": report.title,
        },
        url=f"/etvous/{report.pk}/",
        report=report,
        email_subject=_("Nouveau commentaire — %(title)s") % {"title": report.title},
        email_template="new_comment",
        email_context={
            "report": report,
            "comment": comment,
            "author": author,
        },
    )


def notify_assignment(report, assigned_to, assigned_by):
    """Notifie l'élu assigné."""
    if assigned_to == assigned_by:
        return

    notify(
        recipient=assigned_to,
        notification_type=Notification.Type.ASSIGNMENT,
        title=_("Nouvelle affectation : %(title)s") % {"title": report.title},
        message=_("Vous avez été désigné(e) pour traiter la sollicitation « %(title)s ».") % {
            "title": report.title,
        },
        url=f"/etvous/tableau-de-bord/{report.pk}/",
        report=report,
        email_subject=_("Affectation — %(title)s") % {"title": report.title},
        email_template="assignment",
        email_context={
            "report": report,
            "assigned_by": assigned_by,
        },
    )


def notify_new_report(report):
    """Notifie le maire et les élus qu'une nouvelle sollicitation a été créée."""
    recipients = User.objects.filter(
        role__in=[User.Role.MAYOR, User.Role.ELECTED],
        is_approved=True,
    ).exclude(pk=report.author_id)

    for recipient in recipients:
        notify(
            recipient=recipient,
            notification_type=Notification.Type.NEW_REPORT,
            title=_("Nouvelle sollicitation : %(title)s") % {"title": report.title},
            message=_("Nouvelle sollicitation de %(author)s : « %(title)s »") % {
                "author": report.author.get_full_name(),
                "title": report.title,
            },
            url=f"/etvous/tableau-de-bord/{report.pk}/",
            report=report,
            email_subject=_("Nouvelle sollicitation — %(title)s") % {"title": report.title},
            email_template="new_report",
            email_context={"report": report},
        )


def notify_new_registration(new_user):
    """Notifie les admins d'une nouvelle inscription."""
    recipients = User.objects.filter(
        role=User.Role.ADMIN,
        is_approved=True,
    )
    for recipient in recipients:
        notify(
            recipient=recipient,
            notification_type=Notification.Type.NEW_REGISTRATION,
            title=_("Nouvelle inscription : %(name)s") % {"name": new_user.get_full_name()},
            message=_("Nouvelle inscription de %(first)s %(last)s.") % {
                "first": new_user.first_name,
                "last": new_user.last_name,
            },
            url="/admin/accounts/user/?is_approved__exact=0",
            email_subject=_("Nouvelle inscription — %(name)s") % {"name": new_user.get_full_name()},
            email_template="new_registration",
            email_context={"new_user": new_user},
        )


def notify_contact_form(name, email, phone, message_text):
    """Notifie la mairie d'un message via le formulaire de contact."""
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()

    # Notify secretary only (in-app)
    recipients = User.objects.filter(
        role=User.Role.SECRETARY,
        is_approved=True,
    )
    for recipient in recipients:
        notify(
            recipient=recipient,
            notification_type=Notification.Type.CONTACT_FORM,
            title=_("Message de %(name)s") % {"name": name},
            message=message_text[:200],
            url="/admin/",
            email_subject=_("[Contact] Message de %(name)s") % {"name": name},
            email_template="contact_form",
            email_context={
                "name": name,
                "email": email,
                "phone": phone,
                "message_text": message_text,
            },
        )

    # Also send the email to the contact address (for external mailbox)
    send_notification_email(
        type("FakeRecipient", (), {"email": config.email_contact})(),
        _("[Contact] Message de %(name)s") % {"name": name},
        "contact_form",
        {
            "name": name,
            "email": email,
            "phone": phone,
            "message_text": message_text,
        },
    )


def log_action(request, action, target, details=None):
    """Enregistre une action dans le journal d'audit."""
    from .models import AuditLog

    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_type=target.__class__.__name__.lower(),
        target_id=str(target.pk) if hasattr(target, "pk") else "",
        target_label=str(target)[:200],
        details=details or {},
        ip_address=_get_client_ip(request),
    )


def _get_client_ip(request):
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
