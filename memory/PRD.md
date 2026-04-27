# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails. Prepare for on-premise deployment with switchable storage (Emergent / Huawei OBS / S3) and switchable database (MongoDB / Couchbase Enterprise).

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

## Architecture
- **Frontend**: React, React Router, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, Pydantic, reportlab (PDF generation)
- **Database**: Switchable via `DB_TYPE` env var: `mongodb` | `couchbase`
- **Storage**: Switchable via `STORAGE_TYPE` env var: `emergent` | `s3`

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Key Files
- `backend/server.py` — All API endpoints
- `backend/services/database.py` — Database factory + SCOPE_MAP
- `backend/services/db_mongo.py` — MongoDB backend
- `backend/services/db_couchbase.py` — Couchbase backend
- `backend/services/storage.py` — Storage abstraction
- `backend/services/reports.py` — Report generation (CSV + PDF)
- `frontend/src/pages/ReportsPage.jsx` — Reports UI
- `frontend/src/pages/NewDealPage.jsx`, `EditDealPage.jsx`, `DealsPage.jsx`
- `frontend/src/components/DealFormFields.jsx` — Shared form components
- `frontend/src/App.js` — Routes

## What's Been Implemented

### Core Platform (Complete)
- Full auth with JWT, deal CRUD, dashboard, treasury queue, admin pages, file upload

### Performance Optimizations (Complete)
- AbortController, lazy loading, deferred rendering, component memoization

### Bank Account Management (Complete - Mar 17, 2026)
### Deal History Timeline (Complete - Mar 17, 2026)
### Split Settlement Proofs (Complete - Mar 17, 2026)
### Returned Deal Edit Page (Complete - Mar 17, 2026)
### Switchable Storage Abstraction (Complete - Apr 24, 2026)
### Switchable Database Abstraction (Complete - Apr 24, 2026)
- Couchbase scopes: identity, trading, reference, audit

### Reports Feature (Complete - Apr 27, 2026)
- 7 industry-standard FX trading reports, all exportable as CSV + PDF
- **Deal Blotter**: Complete deal log with filters (date, status, client, currency)
- **Settlement Report**: Deals by value date with bank details and proof status
- **Open Positions**: Pending deals by currency pair showing net exposure
- **Transaction Audit Trail**: Full action history (admin only)
- **User Activity**: Per-user action breakdown (admin only)
- **Volume Summary**: Deal counts/volumes grouped by day/week/month
- **Client Activity**: Per-client volume, frequency, average deal size
- PDF branding: Primary #08263e/#ec474e, Secondary #518dca/#f1f2f2
- Dedicated /reports page with role-based visibility
- Backend: 19/19 tests passed

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services modules
- **P2**: Email notifications for deal status changes
