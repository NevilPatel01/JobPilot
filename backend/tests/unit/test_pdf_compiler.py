from pathlib import Path

from app.services.resume import pdf_compiler


def test_resolve_tectonic_prefers_settings_path(monkeypatch, tmp_path):
    binary = tmp_path / "tectonic"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    monkeypatch.setattr(pdf_compiler.settings, "tectonic_path", str(binary))

    assert pdf_compiler.resolve_tectonic_binary() == str(binary)


def test_resolve_tectonic_uses_bundled_binary(monkeypatch, tmp_path):
    binary = tmp_path / "tectonic"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    monkeypatch.setattr(pdf_compiler.settings, "tectonic_path", "")
    monkeypatch.setattr(pdf_compiler.shutil, "which", lambda _: None)
    monkeypatch.setattr(pdf_compiler, "_bundled_tectonic", lambda: binary)
    monkeypatch.setattr(pdf_compiler, "_known_tectonic_paths", lambda: [])

    assert pdf_compiler.resolve_tectonic_binary() == str(binary)


def test_resolve_tectonic_checks_known_service_paths(monkeypatch, tmp_path):
    binary = tmp_path / "tectonic"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    monkeypatch.setattr(pdf_compiler.settings, "tectonic_path", "")
    monkeypatch.setattr(pdf_compiler.shutil, "which", lambda _: None)
    monkeypatch.setattr(pdf_compiler, "_bundled_tectonic", lambda: None)
    monkeypatch.setattr(pdf_compiler, "_known_tectonic_paths", lambda: [Path("/missing/tectonic"), binary])

    assert pdf_compiler.resolve_tectonic_binary() == str(binary)


def test_compile_latex_to_pdf_falls_back_when_tectonic_is_unavailable(monkeypatch):
    monkeypatch.setattr(pdf_compiler.settings, "tectonic_path", "")
    monkeypatch.setattr(pdf_compiler, "resolve_tectonic_candidates", lambda: [])

    pdf = pdf_compiler.compile_latex_to_pdf(r"\section{Summary}Reliable backend preview")

    assert pdf.startswith(b"%PDF-")
    assert b"Reliable backend preview" in pdf


def test_compile_latex_to_pdf_falls_back_when_tectonic_fails(monkeypatch, tmp_path):
    binary = tmp_path / "tectonic"
    binary.write_text("#!/bin/sh\nexit 101\n", encoding="utf-8")
    binary.chmod(0o755)
    monkeypatch.setattr(pdf_compiler, "resolve_tectonic_candidates", lambda: [str(binary)])

    pdf = pdf_compiler.compile_latex_to_pdf(r"\section{Experience}Fallback export")

    assert pdf.startswith(b"%PDF-")
    assert b"Fallback export" in pdf
