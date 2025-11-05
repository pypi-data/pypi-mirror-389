from tlsleuth import __version__


def test_import_package():
    """Verify that the package can be imported and has a version."""
    assert __version__ is not None


def test_version_format():
    """Verify the version format is X.Y.Z"""
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
