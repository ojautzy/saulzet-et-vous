"""Build a structured inventory from the scraped e-monsite HTML files.

Usage:
    python manage.py build_inventory
    python manage.py build_inventory --mirror-dir migration/mirror
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# Mapping: source URL pattern -> target page config
SOURCE_TO_TARGET = {
    "equipe-municipale": {
        "target_page": "mairie/equipe",
        "target_template": "equipe",
        "priority": "CRITIQUE",
    },
    "horaires-et-permanences": {
        "target_page": "mairie/horaires",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "proces-verbaux": {
        "target_page": "mairie/conseil",
        "target_template": "documents",
        "priority": "CRITIQUE",
    },
    "commissions": {
        "target_page": "mairie/commissions",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "etat-civil": {
        "target_page": "demarches/etat-civil",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "carte-identite": {
        "target_page": "demarches/identite",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "urbanisme": {
        "target_page": "demarches/urbanisme",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "plu": {
        "target_page": "demarches/urbanisme",
        "target_template": "documents",
        "priority": "HAUTE",
    },
    "demarches-en-ligne": {
        "target_page": "demarches/en-ligne",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "bulletins-municipaux": {
        "target_page": "documents",
        "target_template": "documents",
        "priority": "HAUTE",
    },
    "la-commune": {
        "target_page": "commune/presentation",
        "target_template": "default",
        "priority": "HAUTE",
    },
    "6-villages": {
        "target_page": "commune/villages",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "acces": {
        "target_page": "commune/acces",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "associations": {
        "target_page": "commune/associations",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "communaute-de-communes": {
        "target_page": "commune/presentation",
        "target_template": "default",
        "priority": "BASSE",
    },
    "jeunesse": {
        "target_page": "vie-quotidienne/jeunesse",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "saint-nectaire": {
        "target_page": "decouvrir/saint-nectaire",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "galerie": {
        "target_page": "decouvrir/galerie",
        "target_template": "default",
        "priority": "BASSE",
    },
    "aide-a-domicile": {
        "target_page": "vie-quotidienne/services",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "portage": {
        "target_page": "vie-quotidienne/services",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "habitat": {
        "target_page": "vie-quotidienne/services",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "dechets": {
        "target_page": "vie-quotidienne/dechets",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "eau": {
        "target_page": "vie-quotidienne/eau",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "assainissement": {
        "target_page": "vie-quotidienne/eau",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "pie-grieche": {
        "target_page": "decouvrir/patrimoine",
        "target_template": "default",
        "priority": "MOYENNE",
    },
    "album": {
        "target_page": "decouvrir/galerie",
        "target_template": "default",
        "priority": "BASSE",
    },
}

# Pages to skip (obsolete content)
SKIP_PATTERNS = [
    "offre-emploi",
    "animations",
    "bafa",
    "associations-slf",
    "narse-espinasse",
    "elections",
    "meteo",
    "newsletter",
    "google-translate",
]


def _get_section_from_url(url):
    """Extract section name from URL path."""
    parts = Path(url).parts
    if len(parts) > 1:
        return parts[1].replace("-", " ").title()
    return "Accueil"


def _match_target(url, title):
    """Match a source URL/title to a target page configuration."""
    url_lower = url.lower()
    title_lower = title.lower() if title else ""

    # Check skip patterns first
    for pattern in SKIP_PATTERNS:
        if pattern in url_lower or pattern in title_lower:
            return None, "supprimer"

    # Match against known patterns
    for pattern, config in SOURCE_TO_TARGET.items():
        if pattern in url_lower or pattern in title_lower:
            return config, "conserver"

    return None, "conserver"


class Command(BaseCommand):
    help = "Construit un inventaire structuré à partir des fichiers HTML aspirés."

    def add_arguments(self, parser):
        parser.add_argument(
            "--mirror-dir",
            type=str,
            default="migration/mirror",
            help="Répertoire contenant les fichiers HTML aspirés",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="migration/migration_inventory.json",
            help="Fichier de sortie JSON",
        )

    def handle(self, *args, **options):
        if BeautifulSoup is None:
            self.stderr.write(
                self.style.ERROR(
                    "beautifulsoup4 est requis. Installez-le : pip install beautifulsoup4"
                )
            )
            return

        mirror_dir = Path(options["mirror_dir"])
        output_path = Path(options["output"])

        if not mirror_dir.exists():
            self.stderr.write(
                self.style.ERROR(
                    f"{mirror_dir} n'existe pas. Lancez d'abord scrape_old_site.sh"
                )
            )
            return

        self.stdout.write("Parcours des fichiers HTML...")
        inventory = []

        for html_file in sorted(mirror_dir.rglob("*.html")):
            try:
                soup = BeautifulSoup(
                    html_file.read_text(errors="ignore"), "html.parser"
                )
            except Exception as e:
                self.stderr.write(f"  Erreur lecture {html_file}: {e}")
                continue

            # Extract title
            title_tag = soup.find("title")
            h1_tag = soup.find("h1")
            title = ""
            if title_tag:
                title = title_tag.get_text(strip=True)
            elif h1_tag:
                title = h1_tag.get_text(strip=True)

            # Extract main content (skip nav, footer, ads)
            for unwanted in soup.find_all(
                ["nav", "footer", "script", "style", "iframe", "noscript"]
            ):
                unwanted.decompose()

            # Remove e-monsite specific elements
            for div in soup.find_all(
                "div", class_=lambda c: c and ("pub" in c or "banner" in c)
            ):
                div.decompose()

            content_text = soup.get_text(strip=True)[:500]

            # Count PDFs and images
            pdf_links = [
                a for a in soup.find_all("a", href=True)
                if a["href"].lower().endswith(".pdf")
            ]
            images = soup.find_all("img", src=True)

            # Determine content type
            if pdf_links and not images:
                content_type = "page_with_pdfs"
            elif images and not pdf_links:
                content_type = "text_with_images"
            elif pdf_links and images:
                content_type = "mixed"
            else:
                content_type = "text_only"

            # Relative URL
            source_url = "/" + str(
                html_file.relative_to(mirror_dir)
            ).replace("\\", "/")
            # Strip the domain directory prefix if present
            if "www.saulzet-le-froid.fr" in source_url:
                source_url = source_url.split("www.saulzet-le-froid.fr")[-1]

            # Match to target
            target_config, suggested_status = _match_target(source_url, title)

            entry = {
                "source_url": source_url,
                "source_title": title,
                "source_section": _get_section_from_url(source_url),
                "content_type": content_type,
                "content_summary": content_text[:200],
                "pdfs_count": len(pdf_links),
                "images_count": len(images),
                "suggested_status": suggested_status,
                "target_page": target_config["target_page"] if target_config else "",
                "target_template": (
                    target_config["target_template"] if target_config else "default"
                ),
                "notes": "",
                "priority": (
                    target_config["priority"] if target_config else "BASSE"
                ),
            }
            inventory.append(entry)

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False))

        self.stdout.write(
            self.style.SUCCESS(
                f"Inventaire généré : {len(inventory)} pages -> {output_path}"
            )
        )

        # Summary
        by_status = {}
        for item in inventory:
            status = item["suggested_status"]
            by_status[status] = by_status.get(status, 0) + 1
        for status, count in sorted(by_status.items()):
            self.stdout.write(f"  {status}: {count}")
