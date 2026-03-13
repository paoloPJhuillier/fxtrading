# FX Trading Tracker - Product Requirements Document

## Original Problem Statement
Mobile-responsive full-stack FX Trading Tracker platform with:
- Secure login with role-based access (Admin, Trader, Treasury Operations)
- Trader: Log Deal Tickets, cancel submitted deals, resubmit returned deals
- Treasury: View/process Deal Tickets (confirm/return), upload settlement proofs, mandatory remarks
- Admin: Manage reference data, manage users, view audit trail
- All roles: Export deal data to CSV
- Crypto + Fiat currency support, Bank/Crypto toggles, "Ours" section
- Server-side pagination, lazy loading, performant UI

## Architecture
- **Backend:** FastAPI + MongoDB (motor) + JWT auth
- **Frontend:** React + TailwindCSS + Shadcn UI
- **Storage:** Emergent Object Storage for settlement proofs
- **DB Collections:** users, deals, audit_logs

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## What's Been Implemented
- [x] Role-based authentication (Admin, Trader, Treasury)
- [x] Complete deal lifecycle: create, review, confirm, return, cancel, resubmit
- [x] Server-side pagination on all tables
- [x] Debounced filter inputs
- [x] CSV export for deals
- [x] Audit trail page (Admin)
- [x] User management (Admin)
- [x] Settlement proof upload (Treasury)
- [x] Bank/Crypto toggle and "Ours" section on deal form
- [x] **P0 Performance Fix (Feb 2026):** React.memo on all table rows (DealRow, TreasuryRow, TxRow, UserRow, AuditRow) + useCallback for handlers. Modal open times reduced from ~12s to <0.2s
- [x] **Dialog Close Overlay Fix (Mar 2026):** Reduced overlay from bg-black/80 to bg-black/40, sped up animation to 150ms, and implemented useRef pattern to preserve dialog content during exit animation. Eliminates black flash on modal close.
- [x] **Comprehensive Performance Overhaul (Mar 2026):**
  - Auth: Reads localStorage immediately, no longer blocks app rendering
  - Code splitting: React.lazy for all page components (reduces initial bundle)
  - Dashboard: Skeleton UI on first load, opacity fade on range change (keeps data visible)
  - All tables: Keep previous data visible during loading (opacity fade instead of blocking spinner)
  - Backend: Dashboard uses MongoDB $facet aggregation (no longer loads all docs into memory)
  - Layout: SidebarContent extracted as memo'd component
  - Dashboard table: RecentDealRow memo'd
  - Eliminated MutationObserver on document.body (was firing on every DOM mutation from dialog/toast portals). Replaced with CSS-only badge hiding.

## P0/P1/P2 Backlog
- No pending issues or feature requests

## Key Files
- `backend/server.py` - All API endpoints
- `frontend/src/pages/DealsPage.jsx` - Trader deals view (DealRow memo)
- `frontend/src/pages/TreasuryPage.jsx` - Treasury review (TreasuryRow memo)
- `frontend/src/pages/TransactionHistoryPage.jsx` - Admin transaction history (TxRow memo)
- `frontend/src/pages/UsersPage.jsx` - Admin user management (UserRow memo)
- `frontend/src/pages/AuditLogPage.jsx` - Admin audit trail (AuditRow memo)
