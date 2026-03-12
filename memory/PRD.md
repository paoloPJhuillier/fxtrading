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

## Implemented Features (All Tested)

### Core Platform
- [x] Role-based access control (Admin, Trader, Treasury)
- [x] JWT authentication with login/logout
- [x] Responsive sidebar navigation per role
- [x] Dashboard with stats, date range toggles
- [x] **Server-side pagination** on all tables (20 rows/page, lazy-loaded)

### Trader Features
- [x] New Deal form with validation, Client Name, searchable dropdowns
- [x] Auto-computation of amount, pre-submission confirmation dialog
- [x] My Deals with filters + Export CSV + **pagination**
- [x] Proof of payment upload/view/delete (pending/returned deals)
- [x] Cancel/Recall with mandatory reason
- [x] Resubmit returned deals
- [x] Bank/Crypto toggle on From/To, Ours section

### Treasury Features
- [x] Deal Queue with Pending/Processed tabs + filters + **pagination**
- [x] Settlement proof upload/view/delete
- [x] Confirm/Return with required remarks + confirmation prompt

### Admin Features
- [x] Reference data management
- [x] User management with search + **pagination**
- [x] Transaction History with Export CSV + **pagination**
- [x] Audit Trail / Activity Log (filterable, paginated)

### Performance
- [x] Server-side pagination: 20 rows per page, only fetches current page
- [x] CSV export still downloads ALL matching records (not just current page)
- [x] Filters reset pagination to page 1

## Key API Endpoints
- POST /api/auth/login
- GET /api/deals (paginated: page, limit, filters) → {deals, total, page, pages}
- GET /api/deals/export (CSV, full dataset)
- POST /api/deals
- GET /api/deals/{deal_id}
- PUT /api/deals/{deal_id}/cancel
- PUT /api/deals/{deal_id}/resubmit
- POST /api/deals/{deal_id}/upload
- DELETE /api/deals/{deal_id}/proofs/{proof_id}
- PUT /api/deals/{deal_id}/process
- GET /api/users (paginated: page, limit, search) → {users, total, page, pages}
- GET /api/audit-logs (paginated)
- GET /api/reference/{entity_type}
- GET /api/dashboard/stats

## Backlog / Future Enhancements
- [ ] Email notifications on deal status changes
- [ ] PDF deal ticket export for printing
- [ ] Dashboard analytics/charts enhancements
- [ ] Deal amendment workflow (edit fields on pending deals)
