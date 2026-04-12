"""Views for the elected officials dashboard."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Case, Count, F, IntegerField, Value, When
from django.db.models.functions import TruncMonth
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.reports.models import Comment, Report
from apps.settings_app.models import Village

from .decorators import admin_required, elected_required, mayor_required

User = get_user_model()


@elected_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Display all reports for elected officials."""
    reports = Report.objects.select_related(
        "author", "assigned_to"
    ).prefetch_related("photos")

    # Status counters (individual variables for easy template access)
    count_new = Report.objects.filter(status=Report.Status.NEW).count()
    count_assigned = Report.objects.filter(status=Report.Status.ASSIGNED).count()
    count_in_progress = Report.objects.filter(status=Report.Status.IN_PROGRESS).count()
    count_resolved = Report.objects.filter(status=Report.Status.RESOLVED).count()
    count_cancelled = Report.objects.filter(status=Report.Status.CANCELLED).count()

    # Filters
    report_type = request.GET.get("type", "")
    status = request.GET.get("status", "")
    assigned = request.GET.get("assigned", "")

    if report_type:
        reports = reports.filter(report_type=report_type)
    if status:
        reports = reports.filter(status=status)
    if assigned:
        reports = reports.filter(assigned_to_id=assigned)

    # Sort: oldest unresolved first (NEW > ASSIGNED > IN_PROGRESS > others)
    reports = reports.annotate(
        status_priority=Case(
            When(status=Report.Status.NEW, then=Value(0)),
            When(status=Report.Status.ASSIGNED, then=Value(1)),
            When(status=Report.Status.IN_PROGRESS, then=Value(2)),
            When(status=Report.Status.RESOLVED, then=Value(3)),
            When(status=Report.Status.CANCELLED, then=Value(4)),
            default=Value(5),
            output_field=IntegerField(),
        )
    ).order_by("status_priority", "created_at")

    elected_users = User.objects.filter(
        role__in=[User.Role.MAYOR, User.Role.ELECTED],
        is_approved=True,
    ).order_by("last_name", "first_name")

    template = "dashboard/dashboard.html"
    if request.headers.get("HX-Request"):
        template = "dashboard/partials/report_cards.html"

    return render(request, template, {
        "reports": reports,
        "count_new": count_new,
        "count_assigned": count_assigned,
        "count_in_progress": count_in_progress,
        "count_resolved": count_resolved,
        "count_cancelled": count_cancelled,
        "current_type": report_type,
        "current_status": status,
        "current_assigned": assigned,
        "report_types": Report.Type.choices,
        "statuses": Report.Status.choices,
        "elected_users": elected_users,
    })


@elected_required
def my_tasks_view(request: HttpRequest) -> HttpResponse:
    """Display reports assigned to the current elected official."""
    reports = Report.objects.filter(
        assigned_to=request.user,
        status__in=[Report.Status.ASSIGNED, Report.Status.IN_PROGRESS],
    ).select_related("author", "assigned_to").prefetch_related("photos")

    reports = reports.annotate(
        status_priority=Case(
            When(status=Report.Status.ASSIGNED, then=Value(0)),
            When(status=Report.Status.IN_PROGRESS, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("status_priority", "created_at")

    template = "dashboard/my_tasks.html"
    if request.headers.get("HX-Request"):
        template = "dashboard/partials/report_cards.html"

    return render(request, template, {"reports": reports})


@elected_required
def detail_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Display report details with elected official actions."""
    report = get_object_or_404(
        Report.objects.select_related(
            "author", "assigned_to", "assigned_by"
        ).prefetch_related("photos", "comments__author"),
        pk=pk,
    )

    elected_users = User.objects.filter(
        role__in=[User.Role.MAYOR, User.Role.ELECTED],
        is_approved=True,
    ).order_by("last_name", "first_name")

    return render(request, "dashboard/detail.html", {
        "report": report,
        "elected_users": elected_users,
    })


@elected_required
@require_POST
def assign_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Assign or take ownership of a report."""
    report = get_object_or_404(Report, pk=pk)

    if report.status != Report.Status.NEW:
        messages.error(request, _("Cette sollicitation ne peut plus être prise en charge."))
        return redirect("dashboard:detail", pk=report.pk)

    # Mayor can assign to another elected official
    assign_to_id = request.POST.get("assign_to")
    if assign_to_id and request.user.is_mayor:
        assign_to = get_object_or_404(User, pk=assign_to_id, is_approved=True)
        if not assign_to.is_elected:
            messages.error(request, _("Cet utilisateur n'est pas un élu."))
            return redirect("dashboard:detail", pk=report.pk)

        old_status = report.status
        report.status = Report.Status.ASSIGNED
        report.assigned_to = assign_to
        report.assigned_by = request.user
        report.assigned_at = timezone.now()
        report.save(update_fields=[
            "status", "assigned_to", "assigned_by", "assigned_at", "updated_at",
        ])

        Comment.objects.create(
            report=report,
            author=request.user,
            content=_("Affecté à %(name)s par %(mayor)s") % {
                "name": assign_to.get_full_name(),
                "mayor": request.user.get_full_name(),
            },
            is_status_change=True,
            old_status=old_status,
            new_status=Report.Status.ASSIGNED,
        )

        from apps.notifications.services import log_action, notify_assignment, notify_status_change

        notify_assignment(report, assign_to, request.user)
        notify_status_change(report, old_status, Report.Status.ASSIGNED, request.user)
        log_action(request, "assign", report, {"assigned_to": assign_to.email})
        messages.success(request, _("Sollicitation affectée avec succès."))
    else:
        # Self-assign (take ownership)
        old_status = report.status
        report.status = Report.Status.ASSIGNED
        report.assigned_to = request.user
        report.assigned_at = timezone.now()
        report.save(update_fields=[
            "status", "assigned_to", "assigned_at", "updated_at",
        ])

        Comment.objects.create(
            report=report,
            author=request.user,
            content=_("Prise en charge par %(name)s") % {
                "name": request.user.get_full_name(),
            },
            is_status_change=True,
            old_status=old_status,
            new_status=Report.Status.ASSIGNED,
        )

        from apps.notifications.services import log_action, notify_status_change

        notify_status_change(report, old_status, Report.Status.ASSIGNED, request.user)
        log_action(request, "assign", report, {"assigned_to": request.user.email})
        messages.success(request, _("Sollicitation prise en charge."))

    return redirect("dashboard:detail", pk=report.pk)


@elected_required
@require_POST
def status_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Change the status of a report (in_progress or resolved)."""
    report = get_object_or_404(Report, pk=pk)

    # Only assigned elected official can change status
    if report.assigned_to != request.user and not request.user.is_mayor:
        messages.error(request, _("Vous n'êtes pas autorisé à modifier cette sollicitation."))
        return redirect("dashboard:detail", pk=report.pk)

    new_status = request.POST.get("new_status")
    comment_text = request.POST.get("comment", "").strip()

    if new_status == Report.Status.IN_PROGRESS:
        if report.status != Report.Status.ASSIGNED:
            messages.error(request, _("Action non autorisée pour ce statut."))
            return redirect("dashboard:detail", pk=report.pk)

        old_status = report.status
        report.status = Report.Status.IN_PROGRESS
        report.save(update_fields=["status", "updated_at"])

        auto_comment = _("Passage en cours de traitement")
        if comment_text:
            auto_comment = f"{auto_comment}\n{comment_text}"

        Comment.objects.create(
            report=report,
            author=request.user,
            content=auto_comment,
            is_status_change=True,
            old_status=old_status,
            new_status=Report.Status.IN_PROGRESS,
        )

        from apps.notifications.services import log_action, notify_status_change

        notify_status_change(report, old_status, Report.Status.IN_PROGRESS, request.user)
        log_action(request, "status_change", report, {"old": old_status, "new": Report.Status.IN_PROGRESS})
        messages.success(request, _("Sollicitation passée en cours de traitement."))

    elif new_status == Report.Status.RESOLVED:
        if report.status not in (Report.Status.ASSIGNED, Report.Status.IN_PROGRESS):
            messages.error(request, _("Action non autorisée pour ce statut."))
            return redirect("dashboard:detail", pk=report.pk)

        resolution_text = request.POST.get("resolution_text", "").strip()
        if not resolution_text:
            messages.error(request, _("La réponse à l'habitant est obligatoire pour clôturer."))
            return redirect("dashboard:detail", pk=report.pk)

        old_status = report.status
        report.status = Report.Status.RESOLVED
        report.resolution_text = resolution_text
        report.resolved_at = timezone.now()
        report.save(update_fields=[
            "status", "resolution_text", "resolved_at", "updated_at",
        ])

        Comment.objects.create(
            report=report,
            author=request.user,
            content=resolution_text,
            is_status_change=True,
            old_status=old_status,
            new_status=Report.Status.RESOLVED,
        )

        from apps.notifications.services import log_action, notify_status_change

        notify_status_change(report, old_status, Report.Status.RESOLVED, request.user)
        log_action(request, "status_change", report, {"old": old_status, "new": Report.Status.RESOLVED})
        messages.success(request, _("Sollicitation clôturée avec succès."))
    else:
        messages.error(request, _("Statut non valide."))

    return redirect("dashboard:detail", pk=report.pk)


@elected_required
@require_POST
def reassign_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Reassign a report to another elected official."""
    report = get_object_or_404(Report, pk=pk)

    if report.status not in (Report.Status.ASSIGNED, Report.Status.IN_PROGRESS):
        messages.error(request, _("Cette sollicitation ne peut pas être réaffectée."))
        return redirect("dashboard:detail", pk=report.pk)

    # Only assigned elected or mayor can reassign
    if report.assigned_to != request.user and not request.user.is_mayor:
        messages.error(request, _("Vous n'êtes pas autorisé à réaffecter cette sollicitation."))
        return redirect("dashboard:detail", pk=report.pk)

    new_assigned_id = request.POST.get("assign_to")
    if not new_assigned_id:
        messages.error(request, _("Veuillez sélectionner un élu."))
        return redirect("dashboard:detail", pk=report.pk)

    new_assigned = get_object_or_404(User, pk=new_assigned_id, is_approved=True)
    if not new_assigned.is_elected:
        messages.error(request, _("Cet utilisateur n'est pas un élu."))
        return redirect("dashboard:detail", pk=report.pk)

    old_assigned = report.assigned_to
    old_status = report.status

    report.assigned_to = new_assigned
    report.assigned_by = request.user
    report.assigned_at = timezone.now()
    report.status = Report.Status.ASSIGNED
    report.save(update_fields=[
        "assigned_to", "assigned_by", "assigned_at", "status", "updated_at",
    ])

    comment_text = request.POST.get("comment", "").strip()
    old_name = old_assigned.get_full_name() if old_assigned else _("personne")
    auto_comment = _("Réaffecté de %(old)s à %(new)s") % {
        "old": old_name,
        "new": new_assigned.get_full_name(),
    }
    if comment_text:
        auto_comment = f"{auto_comment}\n{comment_text}"

    Comment.objects.create(
        report=report,
        author=request.user,
        content=auto_comment,
        is_status_change=True,
        old_status=old_status,
        new_status=Report.Status.ASSIGNED,
    )

    from apps.notifications.services import log_action, notify_assignment

    notify_assignment(report, new_assigned, request.user)
    log_action(request, "assign", report, {"reassigned_from": old_assigned.email if old_assigned else None, "assigned_to": new_assigned.email})
    messages.success(request, _("Sollicitation réaffectée avec succès."))
    return redirect("dashboard:detail", pk=report.pk)


@elected_required
@require_POST
def comment_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Add a comment to a report."""
    report = get_object_or_404(Report, pk=pk)

    if report.status not in (Report.Status.ASSIGNED, Report.Status.IN_PROGRESS):
        messages.error(request, _("Impossible d'ajouter un commentaire à cette sollicitation."))
        return redirect("dashboard:detail", pk=report.pk)

    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, _("Le commentaire ne peut pas être vide."))
        return redirect("dashboard:detail", pk=report.pk)

    comment = Comment.objects.create(
        report=report,
        author=request.user,
        content=content,
        is_status_change=False,
    )

    from apps.notifications.services import notify_new_comment

    notify_new_comment(report, comment, request.user)
    messages.success(request, _("Commentaire ajouté."))
    return redirect("dashboard:detail", pk=report.pk)


@elected_required
@require_POST
def toggle_visibility_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Toggle a report's public/private visibility."""
    report = get_object_or_404(Report, pk=pk)

    report.is_public = not report.is_public
    report.save(update_fields=["is_public", "updated_at"])

    if report.is_public:
        comment_text = _("Sollicitation passée en publique")
    else:
        comment_text = _("Sollicitation passée en privée")

    Comment.objects.create(
        report=report,
        author=request.user,
        content=comment_text,
        is_status_change=False,
    )

    messages.success(request, comment_text)
    return redirect("dashboard:detail", pk=report.pk)


@admin_required
def admin_cleanup_cancelled_view(request: HttpRequest) -> HttpResponse:
    """Delete all cancelled reports."""
    cancelled = Report.objects.filter(status=Report.Status.CANCELLED)
    count = cancelled.count()

    if request.method == "POST":
        cancelled.delete()
        messages.success(
            request,
            _("%(count)s sollicitation(s) annulée(s) supprimée(s).") % {"count": count},
        )
        return redirect("dashboard:admin_cleanup")

    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    return render(request, "dashboard/admin_cleanup.html", {
        "cancelled_count": count,
        "resolved_count": _get_resolved_count(config.cleanup_days),
        "default_days": config.cleanup_days,
    })


@admin_required
def admin_cleanup_resolved_view(request: HttpRequest) -> HttpResponse:
    """Delete resolved reports older than a given delay."""
    try:
        days = max(1, min(int(request.POST.get("days", 30)), 365))
    except (ValueError, TypeError):
        days = 30
    cutoff = timezone.now() - timedelta(days=days)
    resolved = Report.objects.filter(
        status=Report.Status.RESOLVED,
        resolved_at__lt=cutoff,
    )
    count = resolved.count()

    if request.method == "POST":
        resolved.delete()
        messages.success(
            request,
            _("%(count)s sollicitation(s) résolue(s) supprimée(s).") % {"count": count},
        )
        return redirect("dashboard:admin_cleanup")

    return redirect("dashboard:admin_cleanup")


@admin_required
def admin_cleanup_resolved_count_view(request: HttpRequest) -> HttpResponse:
    """Return the count of resolved reports for a given delay (HTMX)."""
    try:
        days = max(1, min(int(request.GET.get("days", 30)), 365))
    except (ValueError, TypeError):
        days = 30
    count = _get_resolved_count(days)
    return HttpResponse(str(count))


def _get_resolved_count(days: int) -> int:
    """Get count of resolved reports older than given days."""
    cutoff = timezone.now() - timedelta(days=days)
    return Report.objects.filter(
        status=Report.Status.RESOLVED,
        resolved_at__lt=cutoff,
    ).count()


@admin_required
def admin_cleanup_view(request: HttpRequest) -> HttpResponse:
    """Display the admin cleanup page."""
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    return render(request, "dashboard/admin_cleanup.html", {
        "cancelled_count": Report.objects.filter(status=Report.Status.CANCELLED).count(),
        "resolved_count": _get_resolved_count(config.cleanup_days),
        "default_days": config.cleanup_days,
    })


@mayor_required
def mayor_dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard enrichi pour le maire avec indicateurs et charge par élu."""
    # Indicateurs globaux
    counts = {}
    for status_value, status_label in Report.Status.choices:
        counts[status_value] = Report.objects.filter(status=status_value).count()
    total = sum(counts.values())

    # Charge par élu
    elected_users = User.objects.filter(
        role__in=[User.Role.MAYOR, User.Role.ELECTED],
        is_approved=True,
    ).order_by("function_order", "last_name")

    elected_workload = []
    for user in elected_users:
        workload = {
            "user": user,
            "assigned": Report.objects.filter(
                assigned_to=user, status=Report.Status.ASSIGNED
            ).count(),
            "in_progress": Report.objects.filter(
                assigned_to=user, status=Report.Status.IN_PROGRESS
            ).count(),
            "resolved": Report.objects.filter(
                assigned_to=user, status=Report.Status.RESOLVED
            ).count(),
        }
        workload["total_active"] = workload["assigned"] + workload["in_progress"]
        elected_workload.append(workload)

    # Sollicitations orphelines
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    orphan_threshold = timezone.now() - timedelta(days=config.orphan_days)
    orphan_reports = Report.objects.filter(
        status=Report.Status.NEW,
        created_at__lt=orphan_threshold,
    ).select_related("author").order_by("created_at")

    # Statistiques
    # Délai moyen de résolution (en jours)
    resolved_reports = Report.objects.filter(
        status=Report.Status.RESOLVED,
        resolved_at__isnull=False,
    )
    avg_resolution = None
    if resolved_reports.exists():
        avg_delta = resolved_reports.aggregate(
            avg_days=Avg(F("resolved_at") - F("created_at"))
        )["avg_days"]
        if avg_delta:
            avg_resolution = avg_delta.days

    # Répartition par type
    type_counts = dict(
        Report.objects.values_list("report_type").annotate(
            count=Count("id")
        ).values_list("report_type", "count")
    )

    # Répartition par village (de l'auteur)
    village_counts = dict(
        Report.objects.exclude(
            author__village__isnull=True
        ).values_list("author__village__name").annotate(
            count=Count("id")
        ).values_list("author__village__name", "count")
    )

    # Nombre par mois (période configurable)
    six_months_ago = timezone.now() - timedelta(days=config.stats_period_days)
    monthly_reports = (
        Report.objects.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    return render(request, "dashboard/mayor_dashboard.html", {
        "counts": counts,
        "total": total,
        "elected_workload": elected_workload,
        "orphan_reports": orphan_reports,
        "avg_resolution": avg_resolution,
        "type_counts": type_counts,
        "village_counts": village_counts,
        "monthly_reports": monthly_reports,
        "report_types": Report.Type.choices,
        "village_choices": [(v.slug, v.name) for v in Village.objects.filter(is_active=True)],
    })


# --- Administration améliorée ---


@mayor_required
def registration_list_view(request: HttpRequest) -> HttpResponse:
    """Liste des inscriptions en attente d'approbation."""
    pending_users = User.objects.filter(is_approved=False).order_by("-created_at")
    return render(request, "dashboard/registration_list.html", {
        "pending_users": pending_users,
    })


@mayor_required
@require_POST
def registration_approve_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Approuver un compte utilisateur."""
    user = get_object_or_404(User, pk=pk, is_approved=False)
    user.is_approved = True
    user.save(update_fields=["is_approved"])

    # Send approval email
    from apps.settings_app.models import SiteSettings

    config = SiteSettings.load()
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    send_mail(
        subject=_("Votre compte a été validé — Saulzet & Vous"),
        message=render_to_string("accounts/emails/account_approved.txt", {"user": user}),
        from_email=config.from_email,
        recipient_list=[user.email],
        fail_silently=True,
    )

    from apps.notifications.services import log_action

    log_action(request, "approve", user)
    messages.success(request, _("Compte de %(name)s approuvé.") % {"name": user.get_full_name()})

    if request.headers.get("HX-Request"):
        return HttpResponse("")
    return redirect("dashboard:registration_list")


@mayor_required
@require_POST
def registration_reject_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Rejeter (supprimer) un compte utilisateur en attente."""
    user = get_object_or_404(User, pk=pk, is_approved=False)
    name = user.get_full_name()
    user.delete()

    messages.success(request, _("Inscription de %(name)s rejetée.") % {"name": name})

    if request.headers.get("HX-Request"):
        return HttpResponse("")
    return redirect("dashboard:registration_list")


@mayor_required
def export_csv_view(request: HttpRequest) -> HttpResponse:
    """Export CSV des sollicitations."""
    import codecs
    import csv

    status_filter = request.GET.get("status", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    reports = Report.objects.select_related("author", "assigned_to").order_by("-created_at")

    if status_filter:
        reports = reports.filter(status=status_filter)
    if date_from:
        reports = reports.filter(created_at__date__gte=date_from)
    if date_to:
        reports = reports.filter(created_at__date__lte=date_to)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="sollicitations.csv"'

    # UTF-8 BOM for Excel
    response.write(codecs.BOM_UTF8.decode("utf-8"))

    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "ID", "Titre", "Type", "Statut", "Auteur", "Village",
        "Élu assigné", "Date création", "Date affectation",
        "Date résolution", "Public/Privé",
    ])

    for report in reports:
        writer.writerow([
            str(report.pk)[:8],
            report.title,
            report.get_report_type_display(),
            report.get_status_display(),
            report.author.get_full_name() if report.author else "",
            str(report.author.village) if report.author and report.author.village else "",
            report.assigned_to.get_full_name() if report.assigned_to else "",
            report.created_at.strftime("%d/%m/%Y %H:%M") if report.created_at else "",
            report.assigned_at.strftime("%d/%m/%Y %H:%M") if report.assigned_at else "",
            report.resolved_at.strftime("%d/%m/%Y %H:%M") if report.resolved_at else "",
            "Public" if report.is_public else "Privé",
        ])

    return response


@admin_required
def audit_log_view(request: HttpRequest) -> HttpResponse:
    """Journal d'audit."""
    from django.core.paginator import Paginator

    from apps.notifications.models import AuditLog

    logs = AuditLog.objects.select_related("user").order_by("-created_at")

    # Filters
    action_filter = request.GET.get("action", "")
    user_filter = request.GET.get("user", "")

    if action_filter:
        logs = logs.filter(action=action_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dashboard/audit_log.html", {
        "page_obj": page_obj,
        "current_action": action_filter,
        "current_user": user_filter,
        "action_choices": AuditLog.Action.choices,
        "staff_users": User.objects.filter(is_approved=True).order_by("last_name"),
    })


@login_required
def documentation_view(request: HttpRequest) -> HttpResponse:
    """Display the user guide matching the current user's role."""
    template_map = {
        "admin": "docs/guide-administrateur.html",
        "secretary": "docs/guide-secretaire.html",
        "mayor": "docs/guide-maire.html",
        "elected": "docs/guide-conseiller.html",
        "citizen": "docs/guide-habitant.html",
    }
    template = template_map.get(request.user.role, "docs/guide-habitant.html")
    return render(request, template)
