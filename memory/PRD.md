# FX Trading Tracker - Product Requirements Document

## Original Problem Statement
Build a mobile-responsive FX Trading Tracker platform with:
- Secure login with role-based access (Admin, Trader, Treasury Operations)
- Trader: Log Deal Tickets with comprehensive fields
- Treasury Operations: View/process Deal Tickets (confirm/return + remarks)
- Admin: Manage reference data, users, and transaction history
- Industry-aligned Forex practices, cryptocurrency support, dashboard date range toggles

## Tech Stack
- **Backend:** FastAPI, MongoDB (motor async), Pydantic, JWT auth, bcrypt
- **Frontend:** React, React Router, TailwindCSS, Shadcn/UI, Sonner toasts
- **File Storage:** Emergent Object Storage (settlement proofs / proof of payment)
- **Architecture:** REST API, decoupled frontend/backend

## User Credentials (Seed Data)
- Admin: admin@fxtracker.com / Admin@123
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123

## Deal Lifecycle Workflow
1. **Trader** creates deal → status: `pending`
2. **Trader** uploads proof of payment on the deal
3. Deal appears in **Treasury's Deal Queue** as `pending`
4. **Treasury** reviews deal + proof of payment:
   - If acceptable → **Confirm** (with required remarks)
   - If unacceptable → **Return** (with required remarks explaining why)
5. If **returned** → deal goes back to **Trader**:
   - Trader sees red alert with treasury's return reason
   - Trader uploads better proof of payment
   - Trader clicks **Resubmit** → status goes back to `pending`
6. **Treasury** reviews again → confirm or return (cycle repeats)
7. **Trader** can also **Cancel/Recall** pending deals with mandatory reason

## Implemented Features (All Tested)

### Core Platform
- [x] Role-based access control (Admin, Trader, Treasury)
- [x] JWT authentication with login/logout
- [x] Responsive sidebar navigation per role
- [x] Dashboard with stats, date range toggles

### Trader Features
- [x] New Deal form with validation, Client Name, searchable dropdowns
- [x] Auto-computation of amount (currency_amount x rate)
- [x] Pre-submission confirmation dialog
- [x] My Deals with filters + Export CSV
- [x] Deal detail with all fields
- [x] **Proof of payment upload/view/delete** (on pending/returned deals)
- [x] Cancel/Recall with mandatory reason
- [x] **Resubmit returned deals** (upload new proof + resubmit)
- [x] Bank/Crypto toggle on From/To sections
- [x] Ours (Receiving Account) section

### Treasury Features
- [x] Deal Queue with Pending/Processed tabs + filters
- [x] Deal review with all details, Ours section, proof of payment
- [x] **Settlement proof upload/view/delete** (treasury side)
- [x] Confirm/Return with required remarks + confirmation prompt
- [x] View cancellation/return reasons

### Admin Features
- [x] Reference data management
- [x] User management (CRUD)
- [x] Transaction History with Export CSV
- [x] Audit Trail / Activity Log (filterable, paginated)

### Deal Form Structure
- [x] Transaction Types: Today, Tomorrow, Spot
- [x] Transfer Types: FX Crypto Conversion, FX Local, PDAX Withdrawal
- [x] Bank/Crypto toggle on From/To/Ours sections

## Key API Endpoints
- POST /api/auth/login
- GET/POST /api/deals, GET /api/deals/{deal_id}
- GET /api/deals/export (CSV)
- PUT /api/deals/{deal_id}/cancel
- PUT /api/deals/{deal_id}/resubmit
- POST /api/deals/{deal_id}/upload
- DELETE /api/deals/{deal_id}/proofs/{proof_id}
- PUT /api/deals/{deal_id}/process
- GET /api/audit-logs
- GET /api/reference/{entity_type}
- GET /api/dashboard/stats

## Backlog / Future Enhancements
- [ ] Email notifications on deal status changes
- [ ] PDF deal ticket export for printing
- [ ] Dashboard analytics/charts enhancements
- [ ] Deal amendment workflow (edit fields on pending deals)
