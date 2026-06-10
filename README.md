# JobPilot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

A free, open-source job search command centre for tech professionals. JobPilot autonomously aggregates remote job listings, provides a Kanban application tracker, resume match scoring, and analytics — all in one dashboard.

> **Paste a job URL, we do the rest.** The URL importer is JobPilot's killer feature — no manual form filling required.

## Features

- **Job Scraper** — RemoteOK, WeWorkRemotely, and Hacker News feeds with smart deduplication
- **Kanban Tracker** — Drag-and-drop pipeline: To Apply → Applied → Interviewing → Offer → Rejected
- **URL Importer** — Paste any careers page URL to auto-fill job details
- **Resume Match Scoring** — TF-IDF keyword matching with visible matched keywords
- **Analytics** — Application trends, interview rate, status breakdown

## Quick Start

```bash
git clone https://github.com/NevilPatel01/JobPilot.git
cd JobPilot
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/health

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including community forums, real-time chat, and job expiry checking.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new job sources and submit pull requests.

## License

[MIT](LICENSE) — free forever.
