# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails. Prepare for on-premise deployment with switchable storage and database backends.

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Architecture
- **Frontend**: React 19.0.0, React Router 7.5.1, TailwindCSS 3.4.17, Shadcn/UI (Radix)
- **Backend**: FastAPI 0.110.1, Pydantic 2.12.5, reportlab 4.4.10
- **Database**: Switchable via DB_TYPE: MongoDB 7.0.31 (motor 3.3.1) | Couchbase Enterprise (SDK 4.6.0)
- **Storage**: Switchable via STORAGE_TYPE: Emergent Object Storage | S3-compatible (boto3 1.42.58)

## What's Been Implemented

### Core Platform (Complete)
- JWT auth, deal CRUD, dashboard, treasury queue, admin pages, file upload

### Performance Optimizations (Complete)
- AbortController, lazy loading, deferred rendering, memoization

### Bank Account Management (Complete - Mar 17, 2026)
### Deal History Timeline (Complete - Mar 17, 2026)
### Split Settlement Proofs (Complete - Mar 17, 2026)
### Returned Deal Edit Page (Complete - Mar 17, 2026)
### Switchable Storage Abstraction (Complete - Apr 24, 2026)
### Switchable Database Abstraction (Complete - Apr 24, 2026)

### Reports Feature (Complete - Apr 28, 2026)
- 7 industry-standard FX trading reports with tabular data view + CSV/PDF export
- Deal Blotter, Settlement, Open Positions, Audit Trail, User Activity, Volume Summary, Client Activity
- **Admin-configurable permissions**: Enable/disable each report per role (trader/treasury/admin)
  - Stored in report_permissions collection
  - Managed via Permissions dialog (admin only)
  - Enforced both server-side and client-side
- **Year-to-Date default date range**: All date filters pre-populated with Jan 1 → today
- PDF branding: Primary #08263e/#ec474e, Secondary #518dca/#f1f2f2
- Tested: 45/45 backend + 16/16 frontend (100%)

### Documentation (Complete - Apr 28, 2026)
- Technical Design Document (PDF + DOCX) — architecture, APIs, data models, security
- Deployment Guide (PDF + DOCX) — prerequisites, env config, network requirements
- Generated in /app/docs/

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services modules
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery (auto-email daily/weekly reports)
