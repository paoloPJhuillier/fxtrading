# FX Trading Tracker - Product Requirements Document

## Original Problem Statement
Build an FX Trading Tracker platform - a mobile-responsive full stack application with role-based access (Admin, Trader, Treasury Operations), deal ticket logging, treasury processing, and admin reference data management.

## Architecture
- **Frontend**: React 19 + Shadcn UI + Tailwind CSS + Recharts
- **Backend**: FastAPI + Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: JWT with role-based access control (admin, trader, treasury)

## User Personas
1. **Trader** - Creates FX deal tickets, monitors deal status
2. **Treasury Operations** - Reviews and processes (confirm/return) pending deals
3. **Admin** - Manages reference data, users, views all transactions

## Core Requirements
- JWT authentication with 3 roles
- Deal ticket CRUD with auto-generated reference numbers (FX-YYYYMMDD-XXXX)
- Enhanced data model: Currency Pair (Buy/Sell), Deal Reference Numbers
- Treasury confirm/return workflow with remarks
- Admin reference data CRUD (Companies, Banks, Transaction Types, Transfer Types, Currencies incl. crypto)
- Role-specific dashboards with date range toggles (7d, 30d, YTD, All Time)
- Pre-loaded currencies (31 fiat + 20 crypto)

## What's Been Implemented (March 2026)
- [x] JWT auth with role-based access
- [x] Login page with demo accounts
- [x] Trader dashboard with metrics & charts
- [x] Deal ticket creation form (sectioned: Deal Info, Amounts, Source, Destination)
- [x] Deal list with status filtering
- [x] Treasury deal queue with confirm/return processing
- [x] Admin reference data management (5 entity types with tabs)
- [x] Admin user management (CRUD)
- [x] Admin transaction history with detail view
- [x] Date range toggles on all dashboards
- [x] Responsive sidebar layout (Sheet on mobile)
- [x] Seed data: 51 currencies, 5 transaction types, 5 transfer types, 5 companies, 6 banks, 3 demo users
- [x] All tests passing (100% backend, 100% frontend)

## Design
- Light corporate theme: Primary #08263e, #ec474e; Secondary #518dca, #f1f2f2
- Fonts: Chivo (headings), Inter (body), JetBrains Mono (data/monospace)
- Fixed sidebar (dark navy) with responsive mobile Sheet

## Prioritized Backlog
### P0 (Critical) - Done
### P1 (Important)
- [ ] Deal ticket editing (before treasury processes)
- [ ] Export transactions to CSV/PDF
- [ ] Pagination for large datasets
### P2 (Nice to Have)
- [ ] Email notifications on deal status changes
- [ ] Audit trail logging
- [ ] Advanced filtering (date range, currency pair, amount range)
- [ ] Multi-currency rate calculator
- [ ] Deal ticket templates for recurring transactions
