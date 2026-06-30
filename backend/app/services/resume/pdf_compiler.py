import io
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def _bundled_tectonic() -> Path | None:
    repo_bin = Path(__file__).resolve().parents[3] / ".bin" / "tectonic"
    if repo_bin.is_file() and os.access(repo_bin, os.X_OK):
        return repo_bin
    return None


def _known_tectonic_paths() -> list[Path]:
    return [
        Path("/usr/local/bin/tectonic"),
        Path("/opt/homebrew/bin/tectonic"),
        Path("/usr/bin/tectonic"),
    ]


def resolve_tectonic_binary() -> str:
    candidates = resolve_tectonic_candidates()
    if candidates:
        return candidates[0]

    raise RuntimeError(
        "Tectonic is not installed or is not visible to the backend process. "
        "Run ./scripts/ensure-tectonic.sh, set TECTONIC_PATH to backend/.bin/tectonic, "
        "then restart the backend service."
    )


def resolve_tectonic_candidates() -> list[str]:
    candidates: list[str] = []

    if settings.tectonic_path:
        path = Path(settings.tectonic_path)
        if path.is_file() and os.access(path, os.X_OK):
            candidates.append(str(path))

    found = shutil.which("tectonic")
    if found:
        candidates.append(found)

    bundled = _bundled_tectonic()
    if bundled:
        candidates.append(str(bundled))

    for candidate in _known_tectonic_paths():
        if candidate.is_file() and os.access(candidate, os.X_OK):
            candidates.append(str(candidate))

    return list(dict.fromkeys(candidates))


def compile_latex_to_pdf_with_status(latex_source: str) -> tuple[bytes, bool]:
    """Compile LaTeX to PDF, returning (pdf_bytes, used_fallback).

    used_fallback is True when Tectonic was unavailable or failed and the
    plain-text fallback PDF was produced instead.
    """
    candidates = resolve_tectonic_candidates()
    errors: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tex_path = Path(tmp) / "resume.tex"
        tex_path.write_text(latex_source, encoding="utf-8")

        for tectonic in candidates:
            try:
                subprocess.run(
                    [tectonic, str(tex_path), "--outdir", tmp],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
                pdf_path = Path(tmp) / "resume.pdf"
                if pdf_path.exists():
                    return pdf_path.read_bytes(), False
                errors.append(f"{tectonic}: PDF was not generated")
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode(errors="replace")[:700] if e.stderr else str(e)
                errors.append(f"{tectonic}: {stderr}")
            except Exception as e:
                errors.append(f"{tectonic}: {e}")

    logger.warning(
        "Tectonic unavailable or failed; serving plain-text fallback PDF. Errors: %s",
        " | ".join(errors) or "no tectonic candidates found",
    )
    return render_latex_fallback_pdf(latex_source, errors), True


def compile_latex_to_pdf(latex_source: str) -> bytes:
    pdf_bytes, _ = compile_latex_to_pdf_with_status(latex_source)
    return pdf_bytes


def _decode_latex_text(text: str) -> str:
    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\$": "$",
        r"\#": "#",
        r"\_": "_",
        r"\{": "{",
        r"\}": "}",
        r"\textbackslash{}": "\\",
        r"\textasciitilde{}": "~",
        r"\textasciicircum{}": "^",
    }
    for src, dest in replacements.items():
        text = text.replace(src, dest)
    return text


def _latex_to_plain_text(latex_source: str) -> list[str]:
    text = latex_source
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\href\{[^{}]*\}\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\section\{([^{}]*)\}", r"\n\1\n", text)
    text = re.sub(r"\\resumeSubheading\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}", r"\1 | \3 | \2 | \4", text)
    text = re.sub(r"\\resumeProjectHeading\{([^{}]*)\}\{([^{}]*)\}", r"\1 | \2", text)
    text = re.sub(r"\\resumeItem\{([^{}]*)\}", r"- \1", text)
    text = re.sub(r"\\textbf\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", text)
    text = text.replace(r"\\", "\n")
    text = re.sub(r"[{}$]", "", text)
    text = _decode_latex_text(text)
    lines = [re.sub(r"\s+", " ", line).strip(" -") for line in text.splitlines()]
    cleaned = [line for line in lines if line and line not in {"begin", "end", "document"}]
    return cleaned[:80] or ["Resume preview"]


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_line(text: str, max_chars: int = 92) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current)
            current = word
        else:
            current += " " + word
    lines.append(current)
    return lines


def render_latex_fallback_pdf(latex_source: str, errors: list[str] | None = None) -> bytes:
    lines: list[str] = []
    for line in _latex_to_plain_text(latex_source):
        lines.extend(_wrap_line(line))
    lines = lines[:54]

    stream_lines = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
    for index, line in enumerate(lines):
        if index:
            stream_lines.append("T*")
        stream_lines.append(f"({_pdf_escape(line)}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(pdf)


def extract_pdf_text(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)
