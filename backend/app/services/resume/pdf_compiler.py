import io
import subprocess
import tempfile
from pathlib import Path


def compile_latex_to_pdf(latex_source: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / "resume.tex"
        tex_path.write_text(latex_source, encoding="utf-8")
        try:
            subprocess.run(
                ["tectonic", str(tex_path), "--outdir", tmp],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except FileNotFoundError:
            raise RuntimeError("Tectonic is not installed. Install tectonic for PDF export.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LaTeX compilation failed: {e.stderr.decode()[:500]}")

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
