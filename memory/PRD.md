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
- **File Storage:** Emergent Object Storage (settlement proofs)
- **Architecture:** REST API, decoupled frontend/backend

## User Credentials (Seed Data)
- Admin: admin@fxtracker.com / Admin@123
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123

## Implemented Features (All Tested)

### Core Platform
- [x] Role-based access control (Admin, Trader, Treasury)
- [x] JWT authentication with login/logout
- [x] Responsive sidebar navigation per role
- [x] Dashboard with stats, date range toggles (7d, 30d, YTD)

### Trader Features
- [x] New Deal form with all required fields + validation
- [x] Client Name field in deal lifecycle
- [x] Searchable comboboxes for currencies, companies, banks
- [x] Auto-computation of amount (currency_amount x rate)
- [x] Pre-submission confirmation dialog
- [x] My Deals page with advanced filters + **Export CSV**
- [x] Deal detail view with complete fields
- [x] Cancel/Recall deal with mandatory cancellation reason
- [x] Bank/Crypto toggle on Source (From) & Destination (To)
- [x] Ours (Receiving Account) section

### Treasury Features
- [x] Deal Queue with Pending/Processed tabs + filters
- [x] Deal review dialog with all details, Ours section, settlement proofs
- [x] **Settlement proof upload/view/delete** (treasury-only)
- [x] Confirm/Return with **required** treasury remarks + confirmation prompt
- [x] View cancellation reason for cancelled deals

### Admin Features
- [x] Reference data management
- [x] User management (CRUD)
- [x] Transaction History with **Export CSV**
- [x] **Audit Trail / Activity Log** — logs deal creation, processing, cancellation, proof upload/delete, user CRUD. Filterable by action, entity type, user, date range. Paginated.

### Deal Form Structure
- [x] Transaction Types: Today, Tomorrow, Spot
- [x] Transfer Types: FX Crypto Conversion, FX Local, PDAX Withdrawal
- [x] Bank/Crypto toggle on From/To/Ours sections

### Data
- [x] 31 fiat, 16 stablecoins, 18 crypto currencies
- [x] Companies, banks, transaction types, transfer types

## Key API Endpoints
- POST /api/auth/login
- GET/POST /api/deals, GET /api/deals/{deal_id}
- GET /api/deals/export (CSV)
- PUT /api/deals/{deal_id}/cancel
- POST /api/deals/{deal_id}/upload
- DELETE /api/deals/{deal_id}/proofs/{proof_id}
- PUT /api/deals/{deal_id}/process
- GET /api/audit-logs (admin only, with filtering + pagination)
- GET /api/reference/{entity_type}
- GET /api/dashboard/stats

## Backlog / Future Enhancements
- [ ] Extract helper components for modularity
- [ ] Dashboard enhancements with more analytics/charts
- [ ] Email notifications on deal status changes
- [ ] Deal amendment workflow (edit pending deals)
- [ ] PDF deal ticket export for printing
