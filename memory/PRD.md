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
- [x] New Deal form with all required fields
- [x] Required field validation with error highlighting
- [x] Client Name field in deal lifecycle
- [x] Searchable comboboxes for currencies, companies, banks
- [x] Auto-computation of amount (currency_amount x rate)
- [x] Pre-submission confirmation dialog
- [x] My Deals page with advanced filters (status, client, currency, date range) — includes "cancelled" filter
- [x] Deal detail view with complete fields
- [x] Settlement proof image upload/view/delete
- [x] **Cancel/Recall deal** with mandatory cancellation reason (only for pending deals)

### Treasury Features
- [x] Deal Queue with Pending/Processed tabs
- [x] Advanced filters (client, currency, date range)
- [x] Deal review dialog with all details + settlement proofs + Ours section
- [x] Confirm/Return deals with treasury remarks
- [x] View cancellation reason for cancelled deals

### Admin Features
- [x] Reference data management (companies, banks, transaction/transfer types, currencies)
- [x] User management (CRUD)
- [x] Transaction history view

### Deal Form Enhancements (Latest)
- [x] **Transaction Types:** Today, Tomorrow, Spot
- [x] **Transfer Types:** FX Crypto Conversion, FX Local, PDAX Withdrawal
- [x] **Bank/Crypto Toggle** on Source (From) and Destination (To): Bank shows Bank+Account Number, Crypto shows Wallet Address
- [x] **Ours (Receiving Account) Section:** Bank/Crypto toggle with Bank+Account or Wallet Address — highlighted in yellow in detail views

### Data
- [x] Comprehensive currency seeding (31 fiat, 16 stablecoins, 18 crypto)
- [x] Seeded transaction types (Today, Tomorrow, Spot)
- [x] Seeded transfer types (FX Crypto Conversion, FX Local, PDAX Withdrawal)
- [x] Companies and banks

## Key API Endpoints
- POST /api/auth/login
- GET /api/deals (filters: status, client, currency, date_from, date_to)
- POST /api/deals
- GET /api/deals/{deal_id}
- PUT /api/deals/{deal_id}/cancel (cancellation_reason required)
- POST /api/deals/{deal_id}/upload (settlement proof)
- DELETE /api/deals/{deal_id}/proofs/{proof_id}
- PUT /api/deals/{deal_id}/process
- GET /api/reference/{entity_type}
- GET /api/dashboard/stats

## DB Schema
- **users:** id, email, name, password_hash, role, is_active
- **deals:** id, reference_number, transaction_type, value_date, deal_date, transfer_type, client_name, from_type, from_company, from_bank, from_account_num, from_wallet_address, to_type, to_company, to_bank, to_account_num, to_wallet_address, ours_type, ours_bank, ours_account_num, ours_wallet_address, buy_currency, sell_currency, currency_amount, rate, amount, remarks, status (pending/confirmed/returned/cancelled), treasury_remarks, cancellation_reason, cancelled_at, settlement_proofs[], created_by, created_by_name, processed_by, processed_by_name, processed_at, created_at, updated_at
- **currencies:** id, code, name, type, symbol, is_active
- **companies/banks/transaction_types/transfer_types:** id, name, code, is_active

## Backlog / Future Enhancements
- [ ] Extract helper components (SearchSelect, CurrSel, DatePick) into separate files
- [ ] Dashboard enhancements with more analytics/charts
- [ ] Export deals to CSV/Excel
- [ ] Email notifications on deal status changes
- [ ] Audit trail / activity log
- [ ] Deal amendment workflow (edit pending deals)
