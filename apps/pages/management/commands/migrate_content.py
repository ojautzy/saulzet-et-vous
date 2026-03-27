"""Migrate content from the old e-monsite site to the Django CMS.

Usage:
    python manage.py migrate_content                 # Dry run
    python manage.py migrate_content --execute       # Execute migration
    python manage.py migrate_content --execute --force  # Overwrite existing pages
    python manage.py migrate_content --only mairie/conseil  # Single page
"""

import json
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from apps.pages.models import Document, Page

# URL mapping for internal link rewriting
OLD_URL_TO_NEW = {
    "equipe-municipale": "/mairie/equipe/",
    "horaires-et-permanences": "/mairie/horaires/",
    "proces-verbaux": "/mairie/conseil/",
    "commissions": "/mairie/commissions/",
    "etat-civil": "/demarches/etat-civil/",
    "carte-identite": "/demarches/identite/",
    "urbanisme": "/demarches/urbanisme/",
    "plu": "/demarches/urbanisme/",
    "demarches-en-ligne": "/demarches/en-ligne/",
    "bulletins-municipaux": "/documents/",
    "la-commune": "/commune/presentation/",
    "6-villages": "/commune/villages/",
    "acces": "/commune/acces/",
    "associations": "/commune/associations/",
    "saint-nectaire": "/decouvrir/saint-nectaire/",
    "galerie": "/decouvrir/galerie/",
    "aide-a-domicile": "/vie-quotidienne/services/",
    "portage": "/vie-quotidienne/services/",
    "habitat": "/vie-quotidienne/services/",
    "dechets": "/vie-quotidienne/dechets/",
    "eau": "/vie-quotidienne/eau/",
    "assainissement": "/vie-quotidienne/eau/",
    "pie-grieche": "/decouvrir/patrimoine/",
}

# Template mapping
TEMPLATE_MAP = {
    "equipe": Page.Template.EQUIPE,
    "documents": Page.Template.DOCUMENTS,
    "contact": Page.Template.CONTACT,
    "full_width": Page.Template.FULL_WIDTH,
    "default": Page.Template.DEFAULT,
}

# Category mapping for PDFs based on filename patterns
PDF_CATEGORY_PATTERNS = {
    r"pv|proces.verbal|conseil": Document.Category.PV,
    r"bulletin": Document.Category.BULLETIN,
    r"plu|urbanisme|reglement|zonage": Document.Category.PLU,
    r"arrete": Document.Category.ARRETE,
}


def map_old_url_to_new(href):
    """Map an old e-monsite URL to its new equivalent."""
    href_lower = href.lower()
    for pattern, new_url in OLD_URL_TO_NEW.items():
        if pattern in href_lower:
            return new_url
    return None


def clean_html(raw_html):
    """Clean e-monsite HTML for the Django CMS.

    Produces clean semantic HTML that integrates with Tailwind's
    @tailwindcss/typography `prose` class. All e-monsite proprietary
    markup, styling, tracking elements, and deprecated tags are removed.
    """
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")

    # --- Phase 1: Remove elements that should be completely deleted ---

    # Remove scripts, styles, iframes, noscript
    for tag in soup.find_all(["script", "style", "iframe", "noscript"]):
        tag.decompose()

    # Remove HTML comments (e-monsite metadata, conditional IE blocks)
    from bs4 import Comment

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove e-monsite sidebar (widgets, météo, newsletter, search, etc.)
    for sidebar in soup.find_all("div", class_="sidebar"):
        sidebar.decompose()

    # Remove e-monsite specific elements (ads, banners, widgets, modules)
    emonsite_class_patterns = [
        "pub", "banner", "widget", "e-monsite", "emsp", "emooh",
        "em-module", "em-widget", "em-social", "em-share", "em-cookie",
        "em-popup", "ad-", "google-ad", "quick-access", "carousel",
        "contenuContacts",
    ]
    for el in soup.find_all(
        True,
        class_=lambda c: c
        and any(x in str(c).lower() for x in emonsite_class_patterns),
    ):
        el.decompose()

    # Remove tracking pixels (1x1 or very small images)
    for img in soup.find_all("img"):
        w = img.get("width", "")
        h = img.get("height", "")
        src = img.get("src", "")
        # Remove 1x1 tracking pixels
        if (w in ("1", "0") and h in ("1", "0")) or "tracking" in src.lower():
            img.decompose()
            continue
        # Remove data: URI images (often tracking or placeholder)
        if src.startswith("data:"):
            img.decompose()

    # Remove links with javascript: hrefs
    for link in soup.find_all("a", href=True):
        if link["href"].strip().lower().startswith("javascript:"):
            link.unwrap()

    # Remove links with no href or empty href (navigation artifacts)
    for link in soup.find_all("a"):
        href = link.get("href", "").strip()
        if not href or href == "#":
            link.unwrap()

    # --- Phase 2: Unwrap deprecated/presentational tags (keep content) ---

    deprecated_tags = ["font", "center", "marquee", "blink", "big", "small"]
    for tag_name in deprecated_tags:
        for tag in soup.find_all(tag_name):
            tag.unwrap()

    # --- Phase 3: Strip all attributes except semantic ones ---

    allowed_attrs = {"href", "src", "alt", "title", "width", "height"}
    for tag in soup.find_all(True):
        attrs_to_remove = [attr for attr in tag.attrs if attr not in allowed_attrs]
        for attr in attrs_to_remove:
            del tag[attr]

    # --- Phase 4: Unwrap empty wrapper elements ---

    # Unwrap <span> tags (now attribute-free, they serve no purpose)
    for span in soup.find_all("span"):
        span.unwrap()

    # Remove empty divs (no text, no images, no links)
    # Run twice to catch nested empty divs
    for _ in range(2):
        for div in soup.find_all("div"):
            if not div.get_text(strip=True) and not div.find(["img", "a", "table"]):
                div.decompose()

    # Remove empty paragraphs
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if not text and not p.find(["img", "a"]):
            p.decompose()

    # --- Phase 5: Clean up <br> chains ---

    # Replace 3+ consecutive <br> with a paragraph break
    html_str = str(soup)
    html_str = re.sub(r"(<br\s*/?>[\s\n]*){3,}", "</p><p>", html_str)
    # Replace remaining double <br> with a single paragraph break
    html_str = re.sub(r"(<br\s*/?>[\s\n]*){2}", "</p><p>", html_str)
    # Clean up &nbsp; chains (3+ non-breaking spaces → single space)
    html_str = re.sub(r"(&nbsp;\s*){3,}", " ", html_str)
    soup = BeautifulSoup(html_str, "html.parser")

    # --- Phase 6: Rewrite URLs ---

    # Rewrite internal links to new site structure
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "saulzet-le-froid.fr" in href or (
            not href.startswith("http")
            and not href.startswith("mailto:")
            and not href.startswith("/media/")
        ):
            new_href = map_old_url_to_new(href)
            if new_href:
                link["href"] = new_href

    # Rewrite image paths from e-monsite to local media
    for img in soup.find_all("img", src=True):
        src = img["src"]
        # e-monsite images: /medias/..., or full URLs to their CDN
        if "e-monsite" in src or "/medias/" in src:
            # Extract filename and point to local media
            filename = src.split("/")[-1].split("?")[0]
            if filename:
                img["src"] = f"/media/pages/images/{filename}"
        elif src.startswith("/") and not src.startswith("/media/"):
            filename = src.split("/")[-1].split("?")[0]
            if filename:
                img["src"] = f"/media/pages/images/{filename}"

    # --- Phase 7: Final semantic cleanup ---

    # Convert layout <table> to content (if table has no <th>, it's layout)
    for table in soup.find_all("table"):
        if not table.find("th"):
            # Layout table: extract text content as paragraphs
            rows_text = []
            for row in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                cell_text = " — ".join(c for c in cells if c)
                if cell_text:
                    rows_text.append(f"<p>{cell_text}</p>")
            if rows_text:
                new_content = BeautifulSoup("\n".join(rows_text), "html.parser")
                table.replace_with(new_content)
            else:
                table.decompose()

    # Final pass: remove any remaining empty elements
    result = str(soup).strip()

    # Clean up whitespace artifacts
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def extract_main_content(html_file):
    """Extract the main content area from an e-monsite HTML page.

    e-monsite uses `.view-pages` as the main content container, with
    `.row-container` divs for each content block, and a `.sidebar`
    for widgets. We extract `.view-pages` and strip the sidebar.
    """
    soup = BeautifulSoup(html_file.read_text(errors="ignore"), "html.parser")

    # --- e-monsite primary selectors (confirmed from mirror analysis) ---

    # .view-pages is THE content container on e-monsite
    main = soup.find("div", class_="view-pages")
    if not main:
        main = soup.find("div", class_="view")

    if main:
        # Remove sidebar if it's inside the view (sometimes it is)
        for sidebar in main.find_all("div", class_="sidebar"):
            sidebar.decompose()
        return str(main)

    # --- Fallback selectors for non-standard pages ---

    fallback_selectors = [
        ("div", {"class": re.compile(r"emArticle|emPage", re.I)}),
        ("div", {"class": re.compile(r"em-article|em-page|em-content", re.I)}),
        ("div", {"id": re.compile(r"main-content|page-content", re.I)}),
        ("article", {}),
        ("main", {}),
    ]

    for tag_name, attrs in fallback_selectors:
        el = soup.find(tag_name, attrs) if attrs else soup.find(tag_name)
        if el:
            return str(el)

    # Last resort: get body minus nav/footer/sidebar
    body = soup.find("body")
    if body:
        for unwanted in body.find_all(
            ["nav", "header", "footer", "aside"]
        ):
            unwanted.decompose()
        for nav_el in body.find_all(
            "div",
            class_=lambda c: c
            and any(
                x in str(c).lower()
                for x in [
                    "menu", "nav", "sidebar", "footer", "header",
                    "widget", "quick-access", "horizontal",
                ]
            ),
        ):
            nav_el.decompose()
        return str(body)

    return ""


def guess_pdf_category(filename, link_text=""):
    """Guess the document category from the filename and link text."""
    combined = f"{filename} {link_text}".lower()
    for pattern, category in PDF_CATEGORY_PATTERNS.items():
        if re.search(pattern, combined):
            return category
    return Document.Category.OTHER


def extract_date_from_filename(filename):
    """Try to extract a date from a PDF filename."""
    # Patterns: 2024-03-15, 15-03-2024, 20240315
    patterns = [
        (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),
        (r"(\d{2})-(\d{2})-(\d{4})", "%d-%m-%Y"),
        (r"(\d{2})_(\d{2})_(\d{4})", "%d_%m_%Y"),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                return datetime.strptime(match.group(0), fmt).date()
            except ValueError:
                continue
    return None


class Command(BaseCommand):
    help = "Migre le contenu de l'ancien site e-monsite vers le CMS Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Exécuter réellement la migration (par défaut : dry run)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Écraser les pages existantes ayant le même slug",
        )
        parser.add_argument(
            "--only",
            type=str,
            help="Ne migrer qu'une page spécifique (slug cible, ex: mairie/conseil)",
        )

    def handle(self, *args, **options):
        if BeautifulSoup is None:
            self.stderr.write(
                self.style.ERROR(
                    "beautifulsoup4 est requis. Installez-le : pip install beautifulsoup4"
                )
            )
            return

        execute = options["execute"]
        force = options["force"]
        only = options["only"]

        decisions_path = Path("migration/migration_decisions.json")
        if not decisions_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    "migration/migration_decisions.json n'existe pas. "
                    "Validez d'abord l'inventaire via /admin/migration/"
                )
            )
            return

        decisions = json.loads(decisions_path.read_text())
        mirror_dir = Path("migration/mirror")

        # Filter decisions — include "fusionner" alongside "conserver" and "mettre_a_jour"
        to_migrate = [
            d
            for d in decisions
            if d.get("final_status") in ("conserver", "mettre_a_jour", "fusionner")
            and d.get("final_target")
        ]

        if only:
            to_migrate = [d for d in to_migrate if d.get("final_target") == only]

        if not to_migrate:
            self.stdout.write("Aucune page à migrer.")
            return

        # Group decisions by target to handle merges
        grouped = defaultdict(list)
        for d in to_migrate:
            grouped[d["final_target"]].append(d)

        mode = "EXÉCUTION" if execute else "DRY RUN"
        self.stdout.write(self.style.WARNING(f"\n=== Mode {mode} ==="))
        self.stdout.write(f"{len(to_migrate)} pages à migrer vers {len(grouped)} cibles\n")

        # Show merge groups
        merge_groups = {t: ds for t, ds in grouped.items() if len(ds) > 1}
        if merge_groups:
            self.stdout.write(
                self.style.WARNING(f"  {len(merge_groups)} cibles avec fusion :")
            )
            for target, ds in merge_groups.items():
                sources = ", ".join(d.get("source_title", "?") for d in ds)
                self.stdout.write(f"    /{target}/ ← {sources}")
            self.stdout.write("")

        report = {
            "timestamp": datetime.now().isoformat(),
            "pages_created": 0,
            "pages_skipped": 0,
            "pages_merged": 0,
            "pages_errors": 0,
            "documents_imported": 0,
            "images_imported": 0,
            "pages_to_review": [],
            "errors": [],
            "details": [],
        }

        from apps.accounts.models import User

        admin_user = User.objects.filter(role=User.Role.ADMIN).first()

        for target, target_decisions in grouped.items():
            is_merge = len(target_decisions) > 1
            # Use the first "conserver" entry for title/template, fallback to first
            primary = next(
                (d for d in target_decisions if d.get("final_status") == "conserver"),
                target_decisions[0],
            )
            title = primary.get("source_title", target.split("/")[-1].title())
            template_name = primary.get("target_template", "default")
            source_urls = [d.get("source_url", "") for d in target_decisions]

            label = " + ".join(
                d.get("source_title", "?") for d in target_decisions
            )
            self.stdout.write(f"  {label} -> /{target}/")

            # Parse target slug (possibly with parent)
            parts = target.strip("/").split("/")
            if len(parts) == 2:
                parent_slug, child_slug = parts
            elif len(parts) == 1:
                parent_slug, child_slug = None, parts[0]
            else:
                self.stderr.write(f"    ERREUR: slug invalide '{target}'")
                report["pages_errors"] += 1
                report["errors"].append(
                    {"source": source_urls, "error": f"Invalid slug: {target}"}
                )
                continue

            # Check if page already exists
            existing = Page.objects.filter(slug=child_slug).first()
            if existing and not force:
                self.stdout.write(
                    self.style.NOTICE(f"    SKIP: page '{child_slug}' existe déjà")
                )
                report["pages_skipped"] += 1
                report["details"].append(
                    {"source": source_urls, "target": f"/{target}/", "status": "skipped"}
                )
                continue

            if not execute:
                template = TEMPLATE_MAP.get(template_name, Page.Template.DEFAULT)
                merge_tag = " [FUSION]" if is_merge else ""
                self.stdout.write(
                    f"    Créerait{merge_tag}: slug={child_slug}, "
                    f"parent={parent_slug}, template={template}"
                )
                report["details"].append(
                    {
                        "source": source_urls,
                        "target": f"/{target}/",
                        "status": "would_create",
                        "merge": is_merge,
                    }
                )
                continue

            try:
                # Create parent if needed
                parent_page = None
                if parent_slug:
                    parent_page, created = Page.objects.get_or_create(
                        slug=parent_slug,
                        defaults={
                            "title": parent_slug.replace("-", " ").title(),
                            "is_published": True,
                            "show_in_menu": True,
                            "created_by": admin_user,
                            "updated_by": admin_user,
                        },
                    )
                    if created:
                        self.stdout.write(
                            f"    Créé parent: /{parent_slug}/"
                        )

                # Extract and clean content for each source
                content_parts = []
                for decision in target_decisions:
                    source_url = decision.get("source_url", "")
                    source_title = decision.get("source_title", "")
                    part_content = self._extract_content(mirror_dir, source_url)
                    if part_content:
                        content_parts.append((source_title, part_content))

                # Merge content if multiple sources
                if len(content_parts) > 1:
                    merged_sections = []
                    for section_title, section_content in content_parts:
                        merged_sections.append(
                            f'<h2>{section_title}</h2>\n{section_content}'
                        )
                    content = "\n<hr>\n".join(merged_sections)
                    report["pages_merged"] += 1
                    self.stdout.write(
                        f"    FUSIONNÉ: {len(content_parts)} sources"
                    )
                elif content_parts:
                    content = content_parts[0][1]
                else:
                    content = ""

                template = TEMPLATE_MAP.get(template_name, Page.Template.DEFAULT)
                # Published if any source is "conserver"
                is_published = any(
                    d.get("final_status") == "conserver" for d in target_decisions
                )

                if existing and force:
                    existing.title = title
                    existing.content = content
                    existing.parent = parent_page
                    existing.template = template
                    existing.is_published = is_published
                    existing.updated_by = admin_user
                    existing.save()
                    self.stdout.write(f"    MIS À JOUR: /{target}/")
                else:
                    Page.objects.create(
                        title=title,
                        slug=child_slug,
                        content=content,
                        parent=parent_page,
                        template=template,
                        is_published=is_published,
                        show_in_menu=True,
                        created_by=admin_user,
                        updated_by=admin_user,
                    )
                    self.stdout.write(self.style.SUCCESS(f"    CRÉÉ: /{target}/"))

                report["pages_created"] += 1
                report["details"].append(
                    {
                        "source": source_urls,
                        "target": f"/{target}/",
                        "status": "created",
                        "merge": is_merge,
                    }
                )

                # Flag pages needing review
                needs_review = any(
                    d.get("final_status") in ("mettre_a_jour", "fusionner")
                    for d in target_decisions
                )
                if needs_review:
                    notes = "; ".join(
                        d.get("final_notes", "") for d in target_decisions if d.get("final_notes")
                    )
                    report["pages_to_review"].append(
                        {
                            "slug": target,
                            "reason": notes or "Contenu fusionné/mis à jour — à relire",
                        }
                    )

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"    ERREUR: {e}"))
                report["pages_errors"] += 1
                report["errors"].append({"source": source_urls, "error": str(e)})

        # Import PDFs
        if execute:
            report["documents_imported"] = self._import_documents(admin_user, report)
            report["images_imported"] = self._import_images()

        # Write report
        report_path = Path("migration/migration_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

        self.stdout.write("\n=== Rapport ===")
        self.stdout.write(f"  Pages créées : {report['pages_created']}")
        self.stdout.write(f"  Pages fusionnées : {report['pages_merged']}")
        self.stdout.write(f"  Pages ignorées : {report['pages_skipped']}")
        self.stdout.write(f"  Erreurs : {report['pages_errors']}")
        self.stdout.write(f"  Documents importés : {report['documents_imported']}")
        self.stdout.write(f"  Images importées : {report['images_imported']}")
        if report["pages_to_review"]:
            self.stdout.write(
                f"  Pages à relire : {len(report['pages_to_review'])}"
            )
        self.stdout.write(f"  Rapport : {report_path}")

    def _extract_content(self, mirror_dir, source_url):
        """Extract and clean content from a mirrored HTML file.

        source_url is like /pages/mairie/ouverture-permanence/index.html
        and the file is at mirror/www.saulzet-le-froid.fr/pages/mairie/...
        """
        clean_url = source_url.strip("/")

        # 1. Try exact path match (most reliable)
        exact_path = mirror_dir / "www.saulzet-le-froid.fr" / clean_url
        if exact_path.exists():
            raw_content = extract_main_content(exact_path)
            return clean_html(raw_content)

        # 2. Try matching the last two path components (directory + filename)
        url_parts = clean_url.split("/")
        if len(url_parts) >= 2:
            suffix = "/".join(url_parts[-2:]).lower()
            for html_file in mirror_dir.rglob("*.html"):
                relative = str(html_file.relative_to(mirror_dir)).lower()
                if relative.endswith(suffix):
                    raw_content = extract_main_content(html_file)
                    return clean_html(raw_content)

        # 3. Try filename only as last resort
        filename = url_parts[-1].lower() if url_parts else ""
        if filename and filename != "index.html":
            for html_file in mirror_dir.rglob(filename):
                raw_content = extract_main_content(html_file)
                return clean_html(raw_content)

        return ""

    def _import_documents(self, admin_user, report):
        """Import PDFs from migration/pdfs/ into the Document model."""
        pdf_dir = Path("migration/pdfs")
        if not pdf_dir.exists():
            return 0

        media_docs = Path("media/documents")
        media_docs.mkdir(parents=True, exist_ok=True)

        # Load PDF download log for metadata
        log_path = Path("migration/pdf_download_log.json")
        pdf_log = {}
        if log_path.exists():
            for entry in json.loads(log_path.read_text()):
                local = entry.get("local_path", "")
                if local:
                    pdf_log[Path(local).name] = entry

        count = 0
        for pdf_file in pdf_dir.glob("*.pdf"):
            filename = pdf_file.name

            # Skip if already imported
            if Document.objects.filter(file=f"documents/{filename}").exists():
                continue

            # Copy to media
            dest = media_docs / filename
            shutil.copy2(pdf_file, dest)

            # Determine metadata
            log_entry = pdf_log.get(filename, {})
            link_text = log_entry.get("text", "")
            title = link_text or filename.replace(".pdf", "").replace("_", " ").title()
            category = guess_pdf_category(filename, link_text)
            date = extract_date_from_filename(filename)

            Document.objects.create(
                title=title,
                file=f"documents/{filename}",
                category=category,
                date=date,
                uploaded_by=admin_user,
            )
            count += 1

        return count

    def _import_images(self):
        """Copy images from migration/images/ to media/pages/images/."""
        image_dir = Path("migration/images")
        if not image_dir.exists():
            return 0

        media_images = Path("media/pages/images")
        media_images.mkdir(parents=True, exist_ok=True)

        count = 0
        for img_file in image_dir.iterdir():
            if img_file.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                dest = media_images / img_file.name
                if not dest.exists():
                    shutil.copy2(img_file, dest)
                    count += 1

        return count
