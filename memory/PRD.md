# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management, treasury operations, admin features, and on-premise deployment support.

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

## Architecture
- **Frontend**: React 19.0.0, React Router 7.5.1, TailwindCSS 3.4.17, Shadcn/UI
- **Backend**: FastAPI 0.110.1, Pydantic 2.12.5, reportlab 4.4.10
- **Database**: Switchable (DB_TYPE): MongoDB 7.0.31 | Couchbase Enterprise SDK 4.6.0
- **Storage**: Switchable (STORAGE_TYPE): Emergent Object Storage | S3-compatible (boto3 1.42.58)

## What's Been Implemented

### Core Platform (Complete)
### Performance Optimizations (Complete)
### Bank Account Management (Complete - Mar 17, 2026)
### Deal History Timeline (Complete - Mar 17, 2026)
### Split Settlement Proofs (Complete - Mar 17, 2026)
### Returned Deal Edit Page (Complete - Mar 17, 2026)
### Switchable Storage Abstraction (Complete - Apr 24, 2026)
### Switchable Database Abstraction (Complete - Apr 24, 2026)
### Reports Feature (Complete - Apr 28, 2026)
### Documentation (Complete - Apr 28, 2026)

### FX Assessment Revisions (Complete - May 15, 2026)
9 items from assessment implemented and tested:

1. **Client Settlement — Trader Only**: Treasury can only view client proofs, not upload. Upload button removed from Treasury review. Server blocks client proof upload for non-traders.
2. **Deal History Column**: "Last Action" column in My Deals table showing colored badges (created, confirmed, returned, proof uploaded). History truncated to last 3 entries in list API.
3. **Currency Conversion — SALE Perspective (÷)**: When Buy Currency = PHP and Sell Currency is any other currency, formula auto-switches to division.
4. **Auto-Detect Divide Formula**: Blue info box appears when auto-divide mode is active. Rate summary shows ÷ instead of ×.
5. **Auto-Format Numbers with Commas**: Currency Amount shows comma-formatted helper text. Converted Amount field displays with Intl.NumberFormat.
6. **New Transfer Type: FX Bank Deal**: Seeded in DB. Available in Transfer Type dropdown.
7. **Deactivate Destination (To) for FX Bank Deal**: When FX Bank Deal selected, Destination section hidden and replaced with "not applicable" notice. Server coerces destination fields to empty.
8. **Deactivate Client Settlement Proofs for FX Bank Deal**: Client's Settlement upload hidden for FX Bank Deal. Server blocks client proof uploads for FX Bank Deal deals.
9. **Disable Confirm Without Proofs**: Treasury Confirm button disabled when zero settlement proofs. Amber message "Settlement proofs required to confirm" shown. Server enforces: 400 error if confirming with 0 proofs.

Server-side enforcement added for items 6-9 (not just UI):
- FX Bank Deal → destination fields coerced to empty on create
- FX Bank Deal → client proof upload blocked (400)
- Confirm → blocked without proofs (400)

Tested: 7/7 backend + 9/9 frontend items (100%)

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services
- **P1**: Extract shared deal formula logic into useDealFormulas hook (DRY)
- **P2**: Move aggregation reports to MongoDB $group pipelines
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery
