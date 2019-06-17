import pytest
import httpmocker


def test_project_defines_author_and_version():
    assert hasattr(httpmocker, "__author__")
    assert hasattr(httpmocker, "__version__")
