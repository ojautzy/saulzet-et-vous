"""Views for the CMS pages app."""

import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from .forms import ContactForm
from .models import Document, Page


def home_view(request):
    """Page d'accueil portail communal."""
    recent_pages = Page.objects.filter(
        is_published=True,
        parent__isnull=False,
    ).order_by("-updated_at")[:4]

    context = {
        "recent_pages": recent_pages,
    }
    return render(request, "home.html", context)


def page_detail_view(request, slug, parent_slug=None):
    """Vue générique pour afficher une page CMS."""
    if parent_slug:
        page = get_object_or_404(
            Page,
            slug=slug,
            parent__slug=parent_slug,
            is_published=True,
        )
    else:
        page = get_object_or_404(Page, slug=slug, parent__isnull=True, is_published=True)

    template_name = f"pages/page_{page.template}.html"
    context = {
        "page": page,
        "documents": page.documents.all() if page.template == Page.Template.DOCUMENTS else None,
    }

    if page.template == Page.Template.EQUIPE:
        from apps.accounts.models import User

        context["team_members"] = User.objects.filter(
            role__in=[User.Role.MAYOR, User.Role.ELECTED],
            is_approved=True,
        ).order_by("function_order", "last_name")

    return render(request, template_name, context)


def contact_view(request):
    """Page de contact avec formulaire."""
    page = Page.objects.filter(slug="contact", is_published=True).first()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            send_mail(
                subject=f"[Saulzet-le-Froid] {form.cleaned_data['subject']}",
                message=form.cleaned_data["message"],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            django_messages.success(request, _("Votre message a bien été envoyé."))
            form = ContactForm()
    else:
        form = ContactForm()
    return render(request, "pages/page_contact.html", {"page": page, "form": form})


def document_list_view(request, category=None):
    """Liste des documents téléchargeables."""
    page = Page.objects.filter(slug="documents", is_published=True).first()
    documents = Document.objects.all()
    if category:
        documents = documents.filter(category=category)
    categories = Document.Category.choices
    return render(request, "pages/page_documents.html", {
        "page": page,
        "documents": documents,
        "categories": categories,
        "current_category": category,
    })


@login_required
def migration_review_view(request):
    """Interface de revue de l'inventaire de migration."""
    if not (request.user.is_admin or request.user.is_mayor):
        return HttpResponseForbidden()

    inventory_path = Path("migration/migration_inventory.json")
    if not inventory_path.exists():
        django_messages.error(
            request, _("L'inventaire n'existe pas. Lancez d'abord build_inventory.")
        )
        return redirect("home")

    inventory = json.loads(inventory_path.read_text())

    decisions_path = Path("migration/migration_decisions.json")

    if request.method == "POST":
        decisions = []
        for i, item in enumerate(inventory):
            status = request.POST.get(f"status_{i}", item["suggested_status"])
            target = request.POST.get(f"target_{i}", item.get("target_page", ""))
            notes = request.POST.get(f"notes_{i}", item.get("notes", ""))
            decisions.append(
                {
                    **item,
                    "final_status": status,
                    "final_target": target,
                    "final_notes": notes,
                }
            )
        decisions_path.write_text(
            json.dumps(decisions, indent=2, ensure_ascii=False)
        )
        django_messages.success(request, _("Décisions de migration enregistrées."))

    # Apply saved decisions to inventory (both after POST and on GET)
    if decisions_path.exists():
        saved_decisions = json.loads(decisions_path.read_text())
        saved_by_url = {d.get("source_url"): d for d in saved_decisions}
        for item in inventory:
            saved = saved_by_url.get(item.get("source_url"))
            if saved:
                item["suggested_status"] = saved.get(
                    "final_status", item.get("suggested_status")
                )
                item["target_page"] = saved.get(
                    "final_target", item.get("target_page", "")
                )
                item["notes"] = saved.get(
                    "final_notes", item.get("notes", "")
                )

    # Compute stats after applying decisions
    stats = {"conserver": 0, "mettre_a_jour": 0, "supprimer": 0, "fusionner": 0}
    for item in inventory:
        status = item.get("suggested_status", "conserver")
        if status in stats:
            stats[status] += 1

    return render(
        request, "migration/review.html", {"inventory": inventory, "stats": stats}
    )

