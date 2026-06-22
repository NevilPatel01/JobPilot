import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings


def _bundled_tectonic() -> Path | None:
    repo_bin = Path(__file__).resolve().parents[3] / ".bin" / "tectonic"
    if repo_bin.is_file() and os.access(repo_bin, os.X_OK):
        return repo_bin
    return None


def resolve_tectonic_binary() -> str:
    if settings.tectonic_path:
        path = Path(settings.tectonic_path)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        raise RuntimeError(f"Tectonic not found at TECTONIC_PATH={settings.tectonic_path}")

    found = shutil.which("tectonic")
    if found:
        return found

    bundled = _bundled_tectonic()
    if bundled:
        return str(bundled)

    raise RuntimeError(
        "Tectonic is not installed. Run ./scripts/ensure-tectonic.sh or install tectonic for PDF export."
    )


def compile_latex_to_pdf(latex_source: str) -> bytes:
    tectonic = resolve_tectonic_binary()
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / "resume.tex"
        tex_path.write_text(latex_source, encoding="utf-8")
        try:
            subprocess.run(
                [tectonic, str(tex_path), "--outdir", tmp],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode(errors="replace")[:500] if e.stderr else str(e)
            raise RuntimeError(f"LaTeX compilation failed: {stderr}") from e

        pdf_path = Path(tmp) / "resume.pdf"
        if not pdf_path.exists():
            raise RuntimeError("PDF was not generated")
        return pdf_path.read_bytes()


def extract_pdf_text(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)
