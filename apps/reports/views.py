"""Views for the reports app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import ReportEditForm, ReportForm
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

            messages.success(request, _("Votre sollicitation a bien été envoyée."))
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
        messages.error(request, _("Cette sollicitation ne peut plus être annulée."))
        return redirect("reports:detail", pk=report.pk)

    old_status = report.status
    report.status = Report.Status.CANCELLED
    report.save(update_fields=["status", "updated_at"])

    Comment.objects.create(
        report=report,
        author=request.user,
        content=_("Sollicitation annulée par l'auteur."),
        is_status_change=True,
        old_status=old_status,
        new_status=Report.Status.CANCELLED,
    )

    messages.success(request, _("Votre sollicitation a été annulée."))
    return redirect("reports:detail", pk=report.pk)


@login_required
def report_edit_view(request: HttpRequest, pk: str) -> HttpResponse:
    """Edit a report (location, photos, visibility only)."""
    report = get_object_or_404(Report, pk=pk, author=request.user)

    if report.status in (Report.Status.RESOLVED, Report.Status.CANCELLED):
        messages.error(request, _("Cette sollicitation ne peut plus être modifiée."))
        return redirect("reports:detail", pk=report.pk)

    if request.method == "POST":
        form = ReportEditForm(request.POST, instance=report)
        if form.is_valid():
            auto_comments = []

            # Check location change
            if form.has_changed() and any(
                f in form.changed_data for f in ("latitude", "longitude", "location_text")
            ):
                auto_comments.append(_("Localisation mise à jour"))

            # Check visibility change
            if "is_public" in form.changed_data:
                if form.cleaned_data["is_public"]:
                    auto_comments.append(_("Sollicitation passée en publique"))
                else:
                    auto_comments.append(_("Sollicitation passée en privée"))

            form.save()

            # Handle new photo uploads
            files = request.FILES.getlist("photos")
            existing_count = report.photos.count()
            if files:
                max_order = existing_count
                for i, f in enumerate(files):
                    if existing_count + i + 1 > 5:
                        break
                    photo = Photo(
                        report=report,
                        original_filename=f.name,
                        order=max_order + i,
                    )
                    photo.image.save(f.name, f, save=False)
                    photo.process_image()
                    photo.save()
                auto_comments.append(_("Photos mises à jour"))

            # Create auto comments
            for comment_text in auto_comments:
                Comment.objects.create(
                    report=report,
                    author=request.user,
                    content=comment_text,
                    is_status_change=False,
                )

            # User comment
            user_comment = request.POST.get("comment", "").strip()
            if user_comment:
                Comment.objects.create(
                    report=report,
                    author=request.user,
                    content=user_comment,
                    is_status_change=False,
                )

            messages.success(request, _("Votre sollicitation a été mise à jour."))
            return redirect("reports:detail", pk=report.pk)
    else:
        form = ReportEditForm(instance=report)

    return render(request, "reports/report_edit.html", {
        "form": form,
        "report": report,
    })


@login_required
@require_POST
def report_delete_photo_view(request: HttpRequest, pk: str, photo_pk: str) -> HttpResponse:
    """Delete a photo from a report."""
    report = get_object_or_404(Report, pk=pk, author=request.user)

    if report.status in (Report.Status.RESOLVED, Report.Status.CANCELLED):
        messages.error(request, _("Cette sollicitation ne peut plus être modifiée."))
        return redirect("reports:edit", pk=report.pk)

    photo = get_object_or_404(Photo, pk=photo_pk, report=report)
    photo.delete()

    Comment.objects.create(
        report=report,
        author=request.user,
        content=_("Photos mises à jour"),
        is_status_change=False,
    )

    messages.success(request, _("Photo supprimée."))
    return redirect("reports:edit", pk=report.pk)


@login_required
def public_reports_view(request: HttpRequest) -> HttpResponse:
    """Display public reports visible to all connected users."""
    reports = Report.objects.filter(
        is_public=True,
        status__in=[Report.Status.ASSIGNED, Report.Status.IN_PROGRESS],
    ).select_related("author").order_by("-created_at")

    # HTMX filter by type
    report_type = request.GET.get("type", "")
    if report_type:
        reports = reports.filter(report_type=report_type)

    template = "reports/public_reports.html"
    if request.headers.get("HX-Request"):
        template = "reports/partials/public_report_cards.html"

    return render(request, template, {
        "reports": reports,
        "current_type": report_type,
        "report_types": Report.Type.choices,
    })
