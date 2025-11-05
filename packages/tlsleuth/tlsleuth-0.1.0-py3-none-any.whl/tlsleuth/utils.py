from pathlib import Path
import importlib.resources as pkg_resources

def load_ascii() -> str:
    """Load ASCII banner from package resources or dev assets."""
    try:
        return pkg_resources.read_text("tlsleuth", "TLSleuthAscii.txt")
    except Exception:
        fallback_path = Path(__file__).parent / "TLSleuthAscii.txt"
        if fallback_path.is_file():
            try:
                return fallback_path.read_text(encoding="utf-8")
            except Exception:
                return "TLSleuth - Banner found but unreadable.\n"
        return "TLSleuth - Banner not found.\n"
