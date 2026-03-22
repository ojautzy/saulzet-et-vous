"""Views for the elected officials dashboard."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Value, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.reports.models import Comment, Report

from .decorators import elected_required

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

    Comment.objects.create(
        report=report,
        author=request.user,
        content=content,
        is_status_change=False,
    )

    messages.success(request, _("Commentaire ajouté."))
    return redirect("dashboard:detail", pk=report.pk)
