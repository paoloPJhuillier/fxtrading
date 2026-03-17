# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails.

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

## Architecture
- **Frontend**: React, React Router, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, MongoDB (motor), Pydantic
- **Storage**: Emergent Object Storage for file uploads

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Key Files
- `backend/server.py` — All API endpoints
- `frontend/src/components/DealFormFields.jsx` — Shared form components (SearchSelect, BankAccountSelect, CurrSel, TypeToggle, DatePick)
- `frontend/src/pages/NewDealPage.jsx` — Create new deal
- `frontend/src/pages/EditDealPage.jsx` — Edit returned deal (same layout as NewDealPage)
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

### Dashboard & Treasury Enhancements (Complete)
- Today/Yesterday shortcuts, Returned tab, Bank Name column, filters, column toggle

---

## Backlog / Future Tasks
- **P3**: Backend refactoring — split server.py into modules
- **P3**: Export deals to CSV/Excel
- **P3**: Email notifications for deal status changes
