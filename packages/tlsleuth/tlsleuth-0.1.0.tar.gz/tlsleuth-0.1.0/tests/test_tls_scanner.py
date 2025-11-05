import pytest

from tlsleuth.scanner import scan_hosts


def test_scan_hosts_example_com():
    """Verify that the scanner returns a dict with expected keys for a valid domain.
    """
    result = scan_hosts("example.com", timeout=5, verbose=False)
    assert isinstance(result, dict)
    for key in ("host", "tls_version", "cipher", "issuer", "valid_until", "cert_expired", "weak_cipher", "error"):
        assert key in result

    if not result.get("error"):
        assert result.get("tls_version")
