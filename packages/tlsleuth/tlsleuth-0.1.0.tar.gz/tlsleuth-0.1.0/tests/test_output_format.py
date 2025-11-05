import os
from pathlib import Path

from tlsleuth.output import print_in_html


def test_html_report_writes_file(tmp_path, monkeypatch):
    """Generating a minimal HTML report and checking for file presence and expected content."""

    monkeypatch.chdir(tmp_path)

    sample = [
        {
            "host": "example.com",
            "tls_version": "TLSv1.3",
            "cipher": "TLS_AES_256_GCM_SHA384",
            "issuer": "CN=Example CA",
            "valid_until": "2099-01-01 00:00:00 UTC",
            "cert_expired": False,
            "weak_cipher": False,
            "error": None,
        }
    ]

    html = print_in_html(sample)

    out_file = Path("tlsleuth_report.html")
    assert out_file.exists(), "The HTML file must be generated in the cwd"

    text = out_file.read_text(encoding="utf-8")
    assert "<html" in text.lower()
    assert "TLSleuth Security Report" in text
    assert "example.com" in text

    assert isinstance(html, str) and "<html" in html.lower()
