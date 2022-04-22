from pathlib import Path

import pytest

from podder_task_foundation_objects_pdf.pdf import PDF


@pytest.fixture
def pdf_path() -> Path:
    return Path(__file__).parent.joinpath("data", "sample.pdf")


def test_pdf_create(pdf_path):
    _object = PDF(path=pdf_path)
    assert _object.type == "pdf"

    file_name = _object.get_file_name()
    assert file_name.name == "sample.pdf"


def test_pdf_get_single_page_pdf(pdf_path):
    _object = PDF(path=pdf_path)
    assert _object.type == "pdf"

    single_page = _object.save_single_page(0)
    assert isinstance(single_page, Path)


def test_pdf_get_multiple_page_pdf(pdf_path):
    _object = PDF(path=pdf_path)
    assert _object.type == "pdf"

    multi_pages = _object.save_multiple_pages([0, 2])
    assert isinstance(multi_pages, Path)
