"""Tests for pages app models."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.pages.models import Document, Page


@pytest.mark.django_db
class TestPage:
    def test_slug_auto_generated(self):
        page = Page.objects.create(title="Ma page de test")
        assert page.slug == "ma-page-de-test"

    def test_slug_not_overwritten(self):
        page = Page.objects.create(title="Ma page", slug="custom-slug")
        assert page.slug == "custom-slug"

    def test_str(self):
        page = Page.objects.create(title="Accueil", slug="accueil")
        assert str(page) == "Accueil"

    def test_get_absolute_url_root(self):
        page = Page.objects.create(title="Contact", slug="contact")
        assert page.get_absolute_url() == "/contact/"

    def test_get_absolute_url_child(self):
        parent = Page.objects.create(title="Mairie", slug="mairie")
        child = Page.objects.create(title="Horaires", slug="horaires", parent=parent)
        assert child.get_absolute_url() == "/mairie/horaires/"

    def test_breadcrumb_root(self):
        page = Page.objects.create(title="Accueil", slug="accueil")
        assert page.breadcrumb == [page]

    def test_breadcrumb_child(self):
        parent = Page.objects.create(title="Mairie", slug="mairie")
        child = Page.objects.create(title="Horaires", slug="horaires", parent=parent)
        assert child.breadcrumb == [parent, child]

    def test_ordering(self):
        p2 = Page.objects.create(title="B", slug="b", menu_order=2)
        p1 = Page.objects.create(title="A", slug="a", menu_order=1)
        pages = list(Page.objects.all())
        assert pages[0] == p1
        assert pages[1] == p2

    def test_parent_children_relation(self):
        parent = Page.objects.create(title="Parent", slug="parent")
        child1 = Page.objects.create(title="Child 1", slug="child-1", parent=parent)
        child2 = Page.objects.create(title="Child 2", slug="child-2", parent=parent)
        assert set(parent.children.all()) == {child1, child2}


@pytest.mark.django_db
class TestDocument:
    def test_str(self):
        doc = Document.objects.create(
            title="PV du 15 mars",
            file=SimpleUploadedFile("test.pdf", b"content"),
            category=Document.Category.PV,
        )
        assert str(doc) == "PV du 15 mars"

    def test_file_extension(self):
        doc = Document.objects.create(
            title="Test",
            file=SimpleUploadedFile("test.pdf", b"content"),
        )
        assert doc.file_extension == "pdf"

    def test_file_size_display(self):
        content = b"x" * 2048
        doc = Document.objects.create(
            title="Test",
            file=SimpleUploadedFile("test.pdf", content),
        )
        assert "Ko" in doc.file_size_display

    def test_category_choices(self):
        assert Document.Category.PV == "pv"
        assert Document.Category.BULLETIN == "bulletin"

    def test_page_association(self):
        page = Page.objects.create(title="Docs", slug="docs")
        doc = Document.objects.create(
            title="Doc 1",
            file=SimpleUploadedFile("doc.pdf", b"content"),
            page=page,
        )
        assert doc in page.documents.all()
