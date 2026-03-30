"""Create the initial page hierarchy for the site.

This command is idempotent: it only creates pages that don't already exist.

Usage:
    python manage.py create_initial_pages              # Create missing pages
    python manage.py create_initial_pages --force       # Recreate all pages
"""

from django.core.management.base import BaseCommand

from apps.pages.models import Page

PLACEHOLDER_CONTENT = (
    '<div class="alert alert-warning">'
    "<p><strong>Page en cours de r\u00e9daction</strong> "
    "\u2014 Ce contenu sera compl\u00e9t\u00e9 prochainement.</p>"
    "</div>"
)

# Map component for the access page
ACCESS_MAP_CONTENT = (
    '<div class="alert alert-warning">'
    "<p><strong>Page en cours de r\u00e9daction</strong> "
    "\u2014 Ce contenu sera compl\u00e9t\u00e9 prochainement.</p>"
    "</div>"
    "\n"
    '<div class="my-6">'
    "{% include 'components/map.html' with editable=False "
    "lat=45.6565 lng=2.9162 zoom=13 map_id='access-map' %}"
    "</div>"
    "<p>La commune de Saulzet-le-Froid est situ\u00e9e dans le Puy-de-D\u00f4me, "
    "entre les Monts Dore et les Monts D\u00f4mes, \u00e0 environ 30 km "
    "au sud-ouest de Clermont-Ferrand.</p>"
)

# Page definitions: (slug, title, template, menu_order, excerpt, content)
# Children are nested under their parent key
PAGES = {
    "mairie": {
        "title": "La mairie",
        "template": "default",
        "menu_order": 10,
        "excerpt": "La mairie de Saulzet-le-Froid : \u00e9quipe municipale, "
        "horaires, conseil et commissions.",
        "content": PLACEHOLDER_CONTENT,
        "children": {
            "equipe": {
                "title": "\u00c9quipe municipale",
                "template": "equipe",
                "menu_order": 10,
                "excerpt": "Le maire et les conseillers municipaux de "
                "Saulzet-le-Froid.",
                "content": "",
            },
            "horaires": {
                "title": "Horaires et permanences",
                "template": "default",
                "menu_order": 20,
                "excerpt": "Horaires d\u2019ouverture de la mairie et "
                "permanences des \u00e9lus.",
                "content": (
                    "<h2>Horaires de la mairie</h2>"
                    "<p>La mairie est ouverte les lundi, mardi, jeudi et vendredi "
                    "de 8h30 \u00e0 12h00.</p>"
                    "<h2>Coordonn\u00e9es</h2>"
                    "<p>Mairie de Saulzet-le-Froid<br>"
                    "Le Bourg<br>"
                    "63710 Saulzet-le-Froid<br>"
                    "T\u00e9l\u00e9phone : 04 73 22 81 65</p>"
                ),
            },
            "conseil": {
                "title": "Conseil municipal",
                "template": "documents",
                "menu_order": 30,
                "excerpt": "Proc\u00e8s-verbaux des s\u00e9ances du conseil municipal.",
                "content": (
                    "<p>Retrouvez ci-dessous les proc\u00e8s-verbaux "
                    "des s\u00e9ances du conseil municipal.</p>"
                ),
            },
            "commissions": {
                "title": "Commissions municipales",
                "template": "default",
                "menu_order": 40,
                "excerpt": "Les commissions municipales et leurs membres.",
                "content": PLACEHOLDER_CONTENT,
            },
        },
    },
    "commune": {
        "title": "La commune",
        "template": "default",
        "menu_order": 20,
        "excerpt": "D\u00e9couvrez Saulzet-le-Froid : pr\u00e9sentation, villages, "
        "acc\u00e8s et associations.",
        "content": PLACEHOLDER_CONTENT,
        "children": {
            "presentation": {
                "title": "Pr\u00e9sentation",
                "template": "default",
                "menu_order": 10,
                "excerpt": "Saulzet-le-Froid, commune du Puy-de-D\u00f4me "
                "de 284 habitants.",
                "content": (
                    "<p>Saulzet-le-Froid est une commune du d\u00e9partement "
                    "du Puy-de-D\u00f4me, en r\u00e9gion Auvergne-Rh\u00f4ne-Alpes. "
                    "La commune compte 284 habitants (recensement 2020) "
                    "r\u00e9partis sur 6 villages.</p>"
                    "<p>Membre de la communaut\u00e9 de communes du Massif du Sancy.</p>"
                ),
            },
            "villages": {
                "title": "Les 6 villages",
                "template": "default",
                "menu_order": 20,
                "excerpt": "Les six villages de la commune : Le Bourg, "
                "Espinat, Mariol, Pailh\u00e8res, Saulzet, Vernines.",
                "content": PLACEHOLDER_CONTENT,
            },
            "acces": {
                "title": "Acc\u00e8s et plans",
                "template": "default",
                "menu_order": 30,
                "excerpt": "Comment venir \u00e0 Saulzet-le-Froid, "
                "carte et itin\u00e9raires.",
                "content": ACCESS_MAP_CONTENT,
            },
            "associations": {
                "title": "Associations",
                "template": "default",
                "menu_order": 40,
                "excerpt": "Les associations de Saulzet-le-Froid.",
                "content": PLACEHOLDER_CONTENT,
            },
        },
    },
    "demarches": {
        "title": "D\u00e9marches administratives",
        "template": "default",
        "menu_order": 30,
        "excerpt": "\u00c9tat civil, pi\u00e8ces d\u2019identit\u00e9, "
        "urbanisme et d\u00e9marches en ligne.",
        "content": PLACEHOLDER_CONTENT,
        "children": {
            "etat-civil": {
                "title": "\u00c9tat civil",
                "template": "default",
                "menu_order": 10,
                "excerpt": "Naissances, mariages, d\u00e9c\u00e8s, "
                "actes d\u2019\u00e9tat civil.",
                "content": PLACEHOLDER_CONTENT,
            },
            "identite": {
                "title": "Pi\u00e8ces d\u2019identit\u00e9",
                "template": "default",
                "menu_order": 20,
                "excerpt": "Carte nationale d\u2019identit\u00e9, passeport.",
                "content": PLACEHOLDER_CONTENT,
            },
            "urbanisme": {
                "title": "Urbanisme et PLU",
                "template": "documents",
                "menu_order": 30,
                "excerpt": "Plan local d\u2019urbanisme, permis de construire, "
                "d\u00e9clarations de travaux.",
                "content": (
                    "<p>Le Plan Local d\u2019Urbanisme (PLU) de "
                    "Saulzet-le-Froid est consultable ci-dessous.</p>"
                ),
            },
            "en-ligne": {
                "title": "D\u00e9marches en ligne",
                "template": "default",
                "menu_order": 40,
                "excerpt": "Services et d\u00e9marches accessibles en ligne.",
                "content": PLACEHOLDER_CONTENT,
            },
        },
    },
    "vie-quotidienne": {
        "title": "Vie quotidienne",
        "template": "default",
        "menu_order": 40,
        "excerpt": "Services, jeunesse, d\u00e9chets, eau et assainissement.",
        "content": PLACEHOLDER_CONTENT,
        "children": {
            "services": {
                "title": "Services \u00e0 la population",
                "template": "default",
                "menu_order": 10,
                "excerpt": "Aide \u00e0 domicile, portage de repas, habitat.",
                "content": PLACEHOLDER_CONTENT,
            },
            "jeunesse": {
                "title": "Jeunesse",
                "template": "default",
                "menu_order": 20,
                "excerpt": "Activit\u00e9s et services pour les jeunes.",
                "content": PLACEHOLDER_CONTENT,
            },
            "dechets": {
                "title": "D\u00e9chets",
                "template": "default",
                "menu_order": 30,
                "excerpt": "Collecte des d\u00e9chets, d\u00e9ch\u00e8teries, tri.",
                "content": PLACEHOLDER_CONTENT,
            },
            "eau": {
                "title": "Eau et assainissement",
                "template": "default",
                "menu_order": 40,
                "excerpt": "Service de l\u2019eau et assainissement.",
                "content": PLACEHOLDER_CONTENT,
            },
        },
    },
    "decouvrir": {
        "title": "D\u00e9couvrir Saulzet",
        "template": "default",
        "menu_order": 50,
        "excerpt": "Patrimoine, AOP Saint-Nectaire, galerie photos.",
        "content": PLACEHOLDER_CONTENT,
        "children": {
            "patrimoine": {
                "title": "Patrimoine naturel et b\u00e2ti",
                "template": "default",
                "menu_order": 10,
                "excerpt": "Le patrimoine de Saulzet-le-Froid : "
                "\u00e9glise, paysages, pie-gri\u00e8che.",
                "content": PLACEHOLDER_CONTENT,
            },
            "saint-nectaire": {
                "title": "AOP Saint-Nectaire",
                "template": "default",
                "menu_order": 20,
                "excerpt": "Le fromage AOP Saint-Nectaire, fiert\u00e9 locale.",
                "content": PLACEHOLDER_CONTENT,
            },
            "galerie": {
                "title": "Galerie photos",
                "template": "galerie",
                "menu_order": 30,
                "excerpt": "Photos de Saulzet-le-Froid et ses environs.",
                "content": PLACEHOLDER_CONTENT,
            },
        },
    },
    "documents": {
        "title": "Documents",
        "template": "documents",
        "menu_order": 60,
        "excerpt": "Proc\u00e8s-verbaux, bulletins municipaux, arr\u00eat\u00e9s "
        "et documents officiels.",
        "content": (
            "<p>Retrouvez l\u2019ensemble des documents officiels "
            "de la commune.</p>"
        ),
        "children": {},
    },
    "contact": {
        "title": "Contact",
        "template": "contact",
        "menu_order": 70,
        "excerpt": "Contactez la mairie de Saulzet-le-Froid.",
        "content": "",
        "children": {},
    },
}


class Command(BaseCommand):
    help = "Crée les pages initiales de l'arborescence du site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recrée toutes les pages (écrase les existantes)",
        )

    def handle(self, *args, **options):
        force = options["force"]
        from apps.accounts.models import User

        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        created_count = 0
        skipped_count = 0
        updated_count = 0

        # First, handle migration of existing equipe-municipale page
        self._migrate_existing_equipe(admin_user)

        for slug, config in PAGES.items():
            result = self._create_page(
                slug=slug,
                config=config,
                parent=None,
                admin_user=admin_user,
                force=force,
            )
            created_count += result["created"]
            skipped_count += result["skipped"]
            updated_count += result["updated"]

            # Create children
            for child_slug, child_config in config.get("children", {}).items():
                parent_page = Page.objects.filter(slug=slug).first()
                result = self._create_page(
                    slug=child_slug,
                    config=child_config,
                    parent=parent_page,
                    admin_user=admin_user,
                    force=force,
                )
                created_count += result["created"]
                skipped_count += result["skipped"]
                updated_count += result["updated"]

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTerminé : {created_count} créées, "
                f"{updated_count} mises à jour, "
                f"{skipped_count} ignorées"
            )
        )

    def _migrate_existing_equipe(self, admin_user):
        """Migrate the existing equipe-municipale page to mairie/equipe."""
        existing = Page.objects.filter(slug="equipe-municipale").first()
        if not existing:
            return

        # Ensure parent /mairie/ exists
        mairie, _ = Page.objects.get_or_create(
            slug="mairie",
            defaults={
                "title": "La mairie",
                "template": Page.Template.DEFAULT,
                "menu_order": 10,
                "is_published": True,
                "show_in_menu": True,
                "created_by": admin_user,
                "updated_by": admin_user,
            },
        )

        # Update the existing page
        existing.slug = "equipe"
        existing.parent = mairie
        existing.updated_by = admin_user
        existing.save()

        self.stdout.write(
            self.style.SUCCESS(
                "  Migré: equipe-municipale -> /mairie/equipe/"
            )
        )

    def _create_page(self, slug, config, parent, admin_user, force):
        """Create a single page. Returns counts dict."""
        result = {"created": 0, "skipped": 0, "updated": 0}

        template = {
            "default": Page.Template.DEFAULT,
            "full_width": Page.Template.FULL_WIDTH,
            "contact": Page.Template.CONTACT,
            "documents": Page.Template.DOCUMENTS,
            "equipe": Page.Template.EQUIPE,
        }.get(config["template"], Page.Template.DEFAULT)

        existing = Page.objects.filter(slug=slug).first()

        if existing and not force:
            path = f"/{parent.slug}/{slug}/" if parent else f"/{slug}/"
            self.stdout.write(f"  SKIP: {path} existe déjà")
            result["skipped"] = 1
            return result

        if existing and force:
            existing.title = config["title"]
            existing.template = template
            existing.menu_order = config["menu_order"]
            existing.excerpt = config.get("excerpt", "")
            existing.content = config.get("content", "")
            existing.parent = parent
            existing.is_published = True
            existing.show_in_menu = True
            existing.updated_by = admin_user
            existing.save()
            path = f"/{parent.slug}/{slug}/" if parent else f"/{slug}/"
            self.stdout.write(f"  MAJ: {path}")
            result["updated"] = 1
            return result

        Page.objects.create(
            title=config["title"],
            slug=slug,
            content=config.get("content", ""),
            excerpt=config.get("excerpt", ""),
            parent=parent,
            template=template,
            menu_order=config["menu_order"],
            is_published=True,
            show_in_menu=True,
            created_by=admin_user,
            updated_by=admin_user,
        )
        path = f"/{parent.slug}/{slug}/" if parent else f"/{slug}/"
        self.stdout.write(self.style.SUCCESS(f"  CRÉÉ: {path}"))
        result["created"] = 1
        return result
