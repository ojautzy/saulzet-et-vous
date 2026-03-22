"""Views for the reports app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import ReportForm
from .models import Comment, Photo, Report


@login_required
def report_list_view(request: HttpRequest) -> HttpResponse:
    """Display the current user's reports."""
    reports = Report.objects.filter(author=request.user).prefetch_related("photos")

    # HTMX partial rendering for filters
    report_type = request.GET.get("type", "")
    status = request.GET.get("status", "")

    if report_type:
        reports = reports.filter(report_type=report_type)
    if status:
        reports = reports.filter(status=status)

    template = "reports/report_list.html"
    if request.headers.get("HX-Request"):
        template = "reports/partials/report_cards.html"

    return render(request, template, {
        "reports": reports,
        "current_type": report_type,
        "current_status": status,
        "report_types": Report.Type.choices,
        "statuses": Report.Status.choices,
    })


@login_required
def report_create_view(request: HttpRequest) -> HttpResponse:
    """Create a new report."""
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.author = request.user
            report.save()

            # Handle photo uploads
            files = request.FILES.getlist("photos")
            for i, f in enumerate(files):
                photo = Photo(
                    report=report,
                    original_filename=f.name,
                    order=i,
                )
                photo.image.save(f.name, f, save=False)
                photo.process_image()
                photo.save()

            messages.success(request, _("Votre sollicitation a bien ete envoyee."))
            return redirect("reports:detail", pk=report.pk)
    else:
        form = ReportForm()

    return render(request, "reports/report_create.html", {"form": form})


@login_required
def report_detail_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Display a report's details."""
    report = get_object_or_404(
        Report.objects.prefetch_related("photos", "comments__author"),
        pk=pk,
        author=request.user,
    )
    return render(request, "reports/report_detail.html", {"report": report})


@login_required
@require_POST
def report_cancel_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Cancel a report (only if status is NEW)."""
    report = get_object_or_404(Report, pk=pk, author=request.user)

    if not report.is_cancellable:
        messages.error(request, _("Cette sollicitation ne peut plus etre annulee."))
        return redirect("reports:detail", pk=report.pk)

    old_status = report.status
    report.status = Report.Status.CANCELLED
    report.save(update_fields=["status", "updated_at"])

    Comment.objects.create(
        report=report,
        author=request.user,
        content=_("Sollicitation annulee par l'auteur."),
        is_status_change=True,
        old_status=old_status,
        new_status=Report.Status.CANCELLED,
    )

    messages.success(request, _("Votre sollicitation a ete annulee."))
    return redirect("reports:detail", pk=report.pk)
