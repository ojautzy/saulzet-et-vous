"""Tests for migration commands and views."""

import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command

from apps.pages.models import Document, Page

# --- clean_html tests ---


class TestCleanHtml:
    def _clean(self, html):
        from apps.pages.management.commands.migrate_content import clean_html

        return clean_html(html)

    def test_removes_scripts(self):
        result = self._clean('<p>Hello</p><script>alert("x")</script>')
        assert "<script>" not in result
        assert "Hello" in result

    def test_removes_styles(self):
        result = self._clean("<style>.foo{}</style><p>Content</p>")
        assert "<style>" not in result
        assert "Content" in result

    def test_removes_iframes(self):
        result = self._clean('<iframe src="http://ads.example.com"></iframe><p>OK</p>')
        assert "<iframe>" not in result
        assert "OK" in result

    def test_preserves_text(self):
        result = self._clean("<p>Le conseil municipal s'est réuni le 15 mars.</p>")
        assert "Le conseil municipal" in result

    def test_preserves_links_href(self):
        result = self._clean('<a href="http://example.com">Lien</a>')
        assert 'href="http://example.com"' in result
        assert "Lien" in result

    def test_preserves_images_src_alt(self):
        result = self._clean('<img src="photo.jpg" alt="Photo du village">')
        assert 'src="photo.jpg"' in result
        assert 'alt="Photo du village"' in result

    def test_removes_inline_styles(self):
        result = self._clean('<p style="color: red; font-size: 12px;">Text</p>')
        assert "style=" not in result
        assert "Text" in result

    def test_removes_css_classes(self):
        result = self._clean('<div class="custom-class foo-bar"><p>Content</p></div>')
        assert "class=" not in result
        assert "Content" in result

    def test_removes_empty_divs(self):
        result = self._clean("<div></div><p>Content</p><div>  </div>")
        assert "Content" in result

    def test_rewrites_internal_links(self):
        result = self._clean(
            '<a href="http://www.saulzet-le-froid.fr/votre-mairie/'
            'les-proces-verbaux-du-conseil-municipal.html">PV</a>'
        )
        assert "/mairie/conseil/" in result

    def test_empty_input(self):
        result = self._clean("")
        assert result == ""

    def test_unwraps_font_tags(self):
        result = self._clean('<font color="red" face="Arial" size="3">Texte</font>')
        assert "<font" not in result
        assert "Texte" in result
        assert "color" not in result

    def test_unwraps_center_tags(self):
        result = self._clean("<center><p>Centré</p></center>")
        assert "<center>" not in result
        assert "Centré" in result

    def test_removes_tracking_pixels(self):
        result = self._clean(
            '<img src="tracking.gif" width="1" height="1"><p>Content</p>'
        )
        assert "tracking.gif" not in result
        assert "Content" in result

    def test_removes_javascript_links(self):
        result = self._clean(
            '<a href="javascript:void(0)">Clic</a><p>OK</p>'
        )
        assert "javascript:" not in result
        assert "Clic" in result

    def test_unwraps_empty_spans(self):
        result = self._clean(
            '<p><span style="color:red">Texte rouge</span> normal</p>'
        )
        assert "<span" not in result
        assert "Texte rouge" in result

    def test_cleans_br_chains(self):
        result = self._clean("<p>Ligne 1</p><br><br><br><br><p>Ligne 2</p>")
        # Should not have 3+ consecutive br tags
        assert "<br" not in result or result.count("<br") < 3

    def test_removes_html_comments(self):
        result = self._clean("<!-- e-monsite tracking --><p>Content</p>")
        assert "<!--" not in result
        assert "Content" in result

    def test_rewrites_emonsite_image_paths(self):
        result = self._clean(
            '<img src="/medias/album/photo.jpg" alt="Photo">'
        )
        assert "/media/pages/images/photo.jpg" in result

    def test_converts_layout_tables_to_paragraphs(self):
        result = self._clean(
            "<table><tr><td>Col 1</td><td>Col 2</td></tr></table>"
        )
        assert "<table" not in result
        assert "Col 1" in result
        assert "Col 2" in result

    def test_preserves_data_tables(self):
        result = self._clean(
            "<table><tr><th>Nom</th><th>Valeur</th></tr>"
            "<tr><td>A</td><td>1</td></tr></table>"
        )
        assert "<table" in result
        assert "Nom" in result

    def test_removes_empty_paragraphs(self):
        result = self._clean("<p></p><p>  </p><p>Content</p>")
        assert "Content" in result
        # Empty paragraphs should be removed
        assert result.count("<p>") <= 2  # only the content paragraph


# --- create_initial_pages tests ---


@pytest.mark.django_db
class TestCreateInitialPages:
    def test_creates_parent_pages(self):
        call_command("create_initial_pages", stdout=StringIO())
        assert Page.objects.filter(slug="mairie", parent__isnull=True).exists()
        assert Page.objects.filter(slug="commune", parent__isnull=True).exists()
        assert Page.objects.filter(slug="demarches", parent__isnull=True).exists()
        assert Page.objects.filter(slug="vie-quotidienne", parent__isnull=True).exists()
        assert Page.objects.filter(slug="decouvrir", parent__isnull=True).exists()
        assert Page.objects.filter(slug="documents", parent__isnull=True).exists()
        assert Page.objects.filter(slug="contact", parent__isnull=True).exists()

    def test_creates_child_pages(self):
        call_command("create_initial_pages", stdout=StringIO())
        mairie = Page.objects.get(slug="mairie")
        assert Page.objects.filter(slug="horaires", parent=mairie).exists()
        assert Page.objects.filter(slug="conseil", parent=mairie).exists()
        assert Page.objects.filter(slug="commissions", parent=mairie).exists()

    def test_correct_templates(self):
        call_command("create_initial_pages", stdout=StringIO())
        assert Page.objects.get(slug="conseil").template == Page.Template.DOCUMENTS
        assert Page.objects.get(slug="contact").template == Page.Template.CONTACT
        assert Page.objects.get(slug="urbanisme").template == Page.Template.DOCUMENTS

    def test_correct_menu_order(self):
        call_command("create_initial_pages", stdout=StringIO())
        mairie = Page.objects.get(slug="mairie")
        commune = Page.objects.get(slug="commune")
        demarches = Page.objects.get(slug="demarches")
        assert mairie.menu_order < commune.menu_order < demarches.menu_order

    def test_idempotent(self):
        call_command("create_initial_pages", stdout=StringIO())
        count_first = Page.objects.count()
        call_command("create_initial_pages", stdout=StringIO())
        count_second = Page.objects.count()
        assert count_first == count_second

    def test_force_recreates(self):
        call_command("create_initial_pages", stdout=StringIO())
        # Modify a page
        page = Page.objects.get(slug="mairie")
        page.title = "Modified"
        page.save()

        call_command("create_initial_pages", "--force", stdout=StringIO())
        page.refresh_from_db()
        assert page.title == "La mairie"

    def test_migrates_existing_equipe_municipale(self):
        # Create old-style page
        Page.objects.create(
            title="Équipe municipale",
            slug="equipe-municipale",
            template=Page.Template.EQUIPE,
            menu_order=10,
        )

        call_command("create_initial_pages", stdout=StringIO())

        # Should be moved to mairie/equipe
        assert not Page.objects.filter(slug="equipe-municipale").exists()
        mairie = Page.objects.get(slug="mairie")
        equipe = Page.objects.get(slug="equipe")
        assert equipe.parent == mairie

    def test_access_page_has_map_content(self):
        call_command("create_initial_pages", stdout=StringIO())
        acces = Page.objects.get(slug="acces")
        assert "45.6565" in acces.content
        assert "map" in acces.content.lower()


# --- migrate_content dry run test ---


@pytest.mark.django_db
class TestMigrateContentDryRun:
    def test_dry_run_creates_nothing(self, tmp_path):
        # Create a minimal decisions file
        decisions = [
            {
                "source_url": "/test-page.html",
                "source_title": "Test Page",
                "final_status": "conserver",
                "final_target": "commune/test",
                "target_template": "default",
            }
        ]
        decisions_path = Path("migration/migration_decisions.json")
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(json.dumps(decisions))

        try:
            initial_count = Page.objects.count()
            call_command("migrate_content", stdout=StringIO())
            assert Page.objects.count() == initial_count
        finally:
            decisions_path.unlink(missing_ok=True)

    def test_execute_creates_pages(self):
        decisions = [
            {
                "source_url": "/test.html",
                "source_title": "Page Test",
                "final_status": "conserver",
                "final_target": "commune/test-migre",
                "target_template": "default",
            }
        ]
        decisions_path = Path("migration/migration_decisions.json")
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(json.dumps(decisions))

        mirror_dir = Path("migration/mirror")
        mirror_dir.mkdir(parents=True, exist_ok=True)

        try:
            call_command("migrate_content", "--execute", stdout=StringIO())
            assert Page.objects.filter(slug="test-migre").exists()
            assert Page.objects.filter(slug="commune").exists()
        finally:
            decisions_path.unlink(missing_ok=True)

    def test_idempotent_without_force(self):
        decisions = [
            {
                "source_url": "/test2.html",
                "source_title": "Page Test 2",
                "final_status": "conserver",
                "final_target": "test-idem",
                "target_template": "default",
            }
        ]
        decisions_path = Path("migration/migration_decisions.json")
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(json.dumps(decisions))

        mirror_dir = Path("migration/mirror")
        mirror_dir.mkdir(parents=True, exist_ok=True)

        try:
            call_command("migrate_content", "--execute", stdout=StringIO())
            count_first = Page.objects.count()
            call_command("migrate_content", "--execute", stdout=StringIO())
            assert Page.objects.count() == count_first
        finally:
            decisions_path.unlink(missing_ok=True)


# --- View tests for migrated pages ---


@pytest.mark.django_db
class TestMigratedPageViews:
    def test_child_page_accessible(self, client):
        parent = Page.objects.create(
            title="Mairie", slug="mairie", is_published=True, menu_order=10
        )
        Page.objects.create(
            title="Horaires",
            slug="horaires",
            parent=parent,
            is_published=True,
            menu_order=20,
        )
        response = client.get("/mairie/horaires/")
        assert response.status_code == 200

    def test_documents_page_shows_docs(self, client):
        from django.core.files.uploadedfile import SimpleUploadedFile

        page = Page.objects.create(
            title="Conseil",
            slug="conseil",
            is_published=True,
            template=Page.Template.DOCUMENTS,
        )
        from apps.pages.models import DocumentCategory
        cat_pv, _ = DocumentCategory.objects.get_or_create(slug="pv", defaults={"name": "PV"})
        Document.objects.create(
            title="PV Mars 2025",
            file=SimpleUploadedFile("pv.pdf", b"content"),
            category=cat_pv,
            page=page,
        )
        # Documents template page accessed at root level
        response = client.get("/conseil/")
        assert response.status_code == 200
        assert response.context["documents"] is not None
        assert response.context["documents"].count() == 1

    def test_menu_contains_pages(self, client):
        Page.objects.create(
            title="La mairie",
            slug="mairie",
            is_published=True,
            show_in_menu=True,
            menu_order=10,
        )
        Page.objects.create(
            title="Contact",
            slug="contact-test",
            is_published=True,
            show_in_menu=True,
            menu_order=70,
        )
        response = client.get("/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "La mairie" in content
