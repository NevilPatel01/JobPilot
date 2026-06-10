---
applyTo: "frontend/**/*.{ts,tsx}"
---

# Frontend (Next.js 14 / TypeScript)

- App Router under `frontend/app/`; dashboard routes in `app/(dashboard)/`
- All API calls through `frontend/lib/api.ts`
- Client components require `"use client"` directive
- Use shared UI: `PageHeader`, `StatCard`, `glass-panel`, `btn-primary`, `btn-secondary`, `input-field` classes from `globals.css`
- Auth: NextAuth with middleware; skip protection when `AUTH_DISABLED=true`
- Match score badges: indigo >60%, amber 30–60%, red <30%
- Kanban: @dnd-kit with status dropdown as drag alternative
