---
applyTo: ".github/**"
---

# GitHub / CI configuration

- CI workflow at `.github/workflows/ci.yml` runs: backend import check, frontend lint+build, Docker image builds
- Do not add secrets to workflow files — use GitHub repository secrets for production deploys
- PR template and issue templates should stay concise and actionable
- Copilot instructions live in `.github/copilot-instructions.md` and `.github/instructions/`
