import pytest
import src.asyc_mock_http


def test_project_defines_author_and_version():
    assert hasattr(src.asyc_mock_http, "__author__")
    assert hasattr(src.asyc_mock_http, "__version__")
