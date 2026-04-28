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
### Performance Optimizations (Complete)
### Bank Account Management (Complete - Mar 17, 2026)
### Deal History Timeline (Complete - Mar 17, 2026)
### Split Settlement Proofs (Complete - Mar 17, 2026)
### Returned Deal Edit Page (Complete - Mar 17, 2026)
### Switchable Storage Abstraction (Complete - Apr 24, 2026)
### Switchable Database Abstraction (Complete - Apr 24, 2026)

### Reports Feature (Complete - Apr 28, 2026)
- 7 industry-standard reports with tabular view + CSV/PDF export
- **Admin-configurable permissions**: Per-role enable/disable via Permissions dialog
- **YTD default date range**: Jan 1 → today
- **Additional filters**: Client Activity (client), Settlement (from/to bank), Audit Trail (user)
- **Server-side pagination**: Deal Blotter, Settlement, Audit Trail use `page`/`limit` params with `count_documents()` for total
- **Server-side sorting**: `sort_by`/`sort_dir` params on paginated reports
- **Debounced search**: 400ms debounce on all text filter inputs (client, currency, bank, user)
- **Aggregation reports** (Volume Summary, Client Activity, User Activity, Open Positions) return bounded summary rows — no pagination needed
- **CSV/PDF exports** always fetch full dataset regardless of current page
- Tested: 16/16 pagination + 8/8 frontend (100%)

### Documentation (Complete - Apr 28, 2026)
- Technical Design Document + Deployment Guide (PDF + DOCX) in /app/docs/

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services
- **P1**: Move aggregation reports to MongoDB $group pipelines for large volumes
- **P2**: Rows-per-page dropdown for paginated reports
- **P2**: Server-side sortable column allowlist per report
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery (auto-email daily/weekly)
