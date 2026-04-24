# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails. Prepare for on-premise deployment with switchable storage (Emergent ↔ Huawei OBS/S3) and switchable database (MongoDB ↔ Couchbase Enterprise).

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

## Architecture
- **Frontend**: React, React Router, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, Pydantic
- **Database**: Switchable via `DB_TYPE` env var:
  - `mongodb` — MongoDB via motor (dev/default)
  - `couchbase` — Couchbase Enterprise SDK 4.x with scopes & collections (on-prem)
- **Storage**: Switchable via `STORAGE_TYPE` env var:
  - `emergent` — Emergent Object Storage (dev/cloud)
  - `s3` — S3-compatible (Huawei OBS, AWS S3, MinIO for on-prem)

## Couchbase Scope/Collection Mapping
| Scope | Collection | MongoDB Equivalent |
|-------|-----------|-------------------|
| identity | users | users |
| trading | deals | deals |
| trading | deal_counters | counters |
| reference | companies | companies |
| reference | banks | banks |
| reference | bank_accounts | bank_accounts |
| reference | currencies | currencies |
| reference | transaction_types | transaction_types |
| reference | transfer_types | transfer_types |
| audit | audit_logs | audit_logs |

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Key Files
- `backend/server.py` — All API endpoints (uses abstracted db/storage)
- `backend/services/database.py` — Database factory, SCOPE_MAP, get_database()
- `backend/services/db_mongo.py` — MongoDB backend (thin motor wrapper)
- `backend/services/db_couchbase.py` — Couchbase backend (N1QL + KV + subdoc)
- `backend/services/storage.py` — Storage abstraction (EmergentStorage, S3Storage)
- `frontend/src/components/DealFormFields.jsx` — Shared form components
- `frontend/src/pages/NewDealPage.jsx` — Create new deal
- `frontend/src/pages/EditDealPage.jsx` — Edit returned deal
- `frontend/src/pages/DealsPage.jsx` — Trader deal list + detail dialog
- `frontend/src/pages/TreasuryPage.jsx` — Treasury deal queue
- `frontend/src/pages/ReferenceDataPage.jsx` — Admin reference data + bank accounts
- `frontend/src/App.js` — Routes including /deals/:id/edit

## What's Been Implemented

### Core Platform (Complete)
- Full auth with JWT, deal CRUD, dashboard, treasury queue, admin pages, file upload

### Performance Optimizations (Complete)
- AbortController, lazy loading, deferred rendering, component memoization

### Bank Account Management (Complete - Mar 17, 2026)
- BankAccountSelect dropdown, inline "Add New Account", admin management dialog

### Deal History Timeline (Complete - Mar 17, 2026)
- Auto-recorded on all deal mutations, visible in detail dialogs

### Split Settlement Proofs (Complete - Mar 17, 2026)
- Client/Processor separate upload sections on all pages

### Returned Deal Edit Page (Complete - Mar 17, 2026)
- Dedicated `/deals/:id/edit` page with identical layout to New Deal page

### Switchable Storage Abstraction (Complete - Apr 24, 2026)
- `backend/services/storage.py`: EmergentStorage + S3Storage via `STORAGE_TYPE` env var
- Tested with MinIO (local S3) and Emergent cloud storage
- `GET /api/storage/status` admin diagnostic endpoint

### Switchable Database Abstraction (Complete - Apr 24, 2026)
- `backend/services/database.py`: Factory with MongoDB and Couchbase backends
- Couchbase uses scopes & collections (identity, trading, reference, audit)
- MongoDB query syntax automatically translated to N1QL for Couchbase
- Supports: find, insert, update ($set/$push/$pull/$unset/$inc), delete, count, aggregate
- Auto-creates scopes, collections, and indexes on first Couchbase startup
- `GET /api/database/status` admin diagnostic endpoint
- Tested end-to-end on both MongoDB and Couchbase Capella (21/21 backend + frontend)

### Dashboard & Treasury Enhancements (Complete)
- Today/Yesterday shortcuts, Returned tab, Bank Name column, filters, column toggle

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services modules
- **P2**: Export deals frontend button (backend CSV endpoint exists)
- **P2**: Email notifications for deal status changes
