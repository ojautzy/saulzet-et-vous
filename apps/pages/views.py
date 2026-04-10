"""Views for the CMS pages app."""

from django.contrib import messages as django_messages
from django.shortcuts import get_object_or_404, render
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
    elif page.template == Page.Template.GALERIE:
        context["gallery_photos"] = page.gallery_photos.filter(
            is_published=True
        ).order_by("order", "-uploaded_at")

    return render(request, template_name, context)


def legal_notice_view(request):
    """Page des mentions légales."""
    return render(request, "pages/legal_notice.html")


def contact_view(request):
    """Page de contact avec formulaire."""
    page = Page.objects.filter(slug="contact", is_published=True).first()
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            from apps.notifications.services import notify_contact_form

            notify_contact_form(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                phone="",
                message_text=f"[{form.cleaned_data['subject']}]\n\n{form.cleaned_data['message']}",
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



