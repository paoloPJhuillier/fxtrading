# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails.

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

## Core Requirements
1. Role-based authentication (Trader, Treasury, Admin)
2. Deal ticket lifecycle: Create → Pending → Processed/Returned/Cancelled
3. Reference data management (Banks, Companies, Currencies, Transaction/Transfer Types)
4. Dashboard with analytics and charts
5. Audit logging of all actions

## Architecture
- **Frontend**: React, React Router, TailwindCSS, Shadcn/UI
- **Backend**: FastAPI, MongoDB (motor), Pydantic
- **Storage**: Emergent Object Storage for file uploads

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Key DB Schema
- **users**: `{username, email, hashed_password, role, first_name, last_name}`
- **deals**: `{..., status, proofs: [{filename, url, proof_type: 'client'|'processor'}], history: [{timestamp, user_email, action, details}]}`
- **bank_accounts**: `{bank_id, account_number, account_name, is_active}`
- **audit_logs**: `{timestamp, user_email, user_role, action, entity_type, entity_id, details}`

---

## What's Been Implemented

### Core Platform (Complete)
- Full auth system with JWT tokens
- Deal ticket CRUD with full lifecycle
- Dashboard with charts and analytics
- Treasury deal queue with tabs (Pending, Processed, Returned)
- Admin pages: Users, Reference Data, Audit Logs
- File upload with Emergent Object Storage

### Performance Optimizations (Complete)
- Removed MutationObserver from index.html
- AbortController cleanup in all useEffect hooks
- Lazy loading with prefetching for pages
- Deferred rendering on heavy pages
- Conditional dialog mounting
- Component memoization throughout

### User Management Enhancements (Complete)
- Split name into first_name/last_name
- Change password feature
- Data migration for existing users

### Bank Account Management (Complete - Mar 17, 2026)
- CRUD API endpoints for bank accounts under banks
- BankAccountSelect dropdown on NewDealPage (auto-loads when bank selected)
- Inline "Add New Account" capability from deal form
- Admin bank accounts management dialog in Reference Data
- Account number auto-clears when bank changes

### Deal History Timeline (Complete - Mar 17, 2026)
- History array on all deals tracking status changes
- Visible in deal detail dialogs (DealsPage + TreasuryPage)
- Auto-recorded on create, confirm, return, cancel, edit, proof upload
- Legacy data backfill on startup

### Split Settlement Proofs (Complete - Mar 17, 2026)
- Separate "Client's Settlement" and "Processor's Settlement" upload sections
- Implemented on NewDealPage, DealsPage, and TreasuryPage
- proof_type parameter on upload API
- Legacy proofs backfilled as 'client' type

### Dashboard & Treasury Enhancements (Complete)
- "Today" and "Yesterday" date shortcuts on Dashboard
- "Returned" tab on Treasury Deal Queue
- Bank Name column, From/To Bank filters
- Column visibility toggle

---

## Backlog / Future Tasks
- **P3**: Backend refactoring — split server.py into routes/, models/, services/
- **P3**: Export deals to CSV/Excel
- **P3**: Email notifications for deal status changes
