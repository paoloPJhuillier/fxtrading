# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails. Prepare for on-premise deployment with switchable storage (Emergent ↔ Huawei OBS/S3) and future DB migration (MongoDB → Couchbase Enterprise).

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

## Architecture
- **Frontend**: React, React Router, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, MongoDB (motor), Pydantic
- **Storage**: Switchable via `STORAGE_TYPE` env var:
  - `emergent` — Emergent Object Storage (dev/cloud)
  - `s3` — S3-compatible (Huawei OBS, AWS S3, MinIO for on-prem)

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Key Files
- `backend/server.py` — All API endpoints
- `backend/services/storage.py` — Storage abstraction layer (EmergentStorage, S3Storage)
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
- All dropdowns (banks, companies, currencies, accounts, types) — prevents typos
- Pre-filled with deal data, treasury return reason shown at top
- "Save Changes" and "Save & Resubmit" buttons
- Shared form components extracted to DealFormFields.jsx (DRY)

### Switchable Storage Abstraction (Complete - Apr 24, 2026)
- `backend/services/storage.py`: ABC interface with EmergentStorage and S3Storage implementations
- Factory singleton pattern via `get_storage()`, driven by `STORAGE_TYPE` env var
- S3 config fully parameterized: `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `S3_REGION`
- Startup validation: fails fast if STORAGE_TYPE=s3 but required S3 env vars are missing
- `DELETE /api/deals/{deal_id}/proofs/{proof_id}` now also removes file from storage backend
- `GET /api/storage/status` admin-only diagnostic endpoint
- Tested 14/14 backend + frontend smoke (100% pass)

### Dashboard & Treasury Enhancements (Complete)
- Today/Yesterday shortcuts, Returned tab, Bank Name column, filters, column toggle

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services modules
- **P1**: Database abstraction prep for Couchbase Enterprise (modular structure, not implementation)
- **P2**: Export deals to CSV/Excel (endpoint exists, needs frontend button)
- **P2**: Email notifications for deal status changes
