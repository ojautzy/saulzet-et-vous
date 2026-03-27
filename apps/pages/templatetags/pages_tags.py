"""Template tags for the pages app."""

from django import template

from apps.pages.models import Page

register = template.Library()


@register.inclusion_tag("components/menu.html")
def site_menu():
    """Génère le menu du site depuis les pages CMS."""
    pages = Page.objects.filter(
        is_published=True,
        show_in_menu=True,
    ).select_related("parent").order_by("menu_order", "title")

    root_pages = []
    children_map = {}
    for page in pages:
        if page.parent_id:
            children_map.setdefault(page.parent_id, []).append(page)
        else:
            root_pages.append(page)

    menu_items = []
    for page in root_pages:
        menu_items.append({
            "page": page,
            "children": children_map.get(page.id, []),
        })

    return {"menu_items": menu_items}


@register.inclusion_tag("components/menu_mobile.html")
def site_menu_mobile():
    """Génère le menu mobile du site depuis les pages CMS."""
    pages = Page.objects.filter(
        is_published=True,
        show_in_menu=True,
    ).select_related("parent").order_by("menu_order", "title")

    root_pages = []
    children_map = {}
    for page in pages:
        if page.parent_id:
            children_map.setdefault(page.parent_id, []).append(page)
        else:
            root_pages.append(page)

    menu_items = []
    for page in root_pages:
        menu_items.append({
            "page": page,
            "children": children_map.get(page.id, []),
        })

    return {"menu_items": menu_items}


@register.inclusion_tag("components/breadcrumb.html")
def breadcrumb(page):
    """Affiche le fil d'Ariane pour une page."""
    return {"crumbs": page.breadcrumb if page else []}
