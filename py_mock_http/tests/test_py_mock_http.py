import pytest
import py_mock_http


def test_project_defines_author_and_version():
    assert hasattr(py_mock_http, "__author__")
    assert hasattr(py_mock_http, "__version__")
