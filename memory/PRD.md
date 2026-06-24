# FX Trading Tracker — PRD

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123
- System Admin: sysadmin@fxtracker.com / SysAdmin@123

## Architecture
- **Frontend**: React 19.0.0, React Router 7.5.1, TailwindCSS 3.4.17, Shadcn/UI
- **Backend**: FastAPI 0.110.1, Pydantic 2.12.5, reportlab 4.4.10
- **Database**: Switchable (DB_TYPE): MongoDB 7.0.31 | Couchbase Enterprise SDK 4.6.0
- **Storage**: Switchable (STORAGE_TYPE): Emergent Object Storage | S3-compatible (boto3 1.42.58)

## Roles
- **Trader**: Create deals, upload client proofs, view own deals, reports
- **Treasury**: Process deals (confirm/return), upload processor proofs, reports
- **Admin**: Manage users, reference data (incl. counterparties), audit trail, report permissions
- **System Admin (sysadmin)**: Everything admin can do + DB reset, DB export, DB stats

## What's Been Implemented (Summary)
- Core Platform, Performance Optimizations, Bank Account Management, Deal History, Split Settlement Proofs, Returned Deal Edit Page
- Switchable Storage (Emergent ↔ S3/Huawei OBS) and Database (MongoDB ↔ Couchbase Enterprise)
- 8 Reports with server-side pagination, debounced filters, autocomplete comboboxes
- Admin-configurable report permissions, YTD default dates
- System Administration (sysadmin role, DB reset, DB export, DB stats)
- FX Assessment 9 Revisions (Items 1-9 from Apr assessment)

### User Feedback 10 Items (Complete - Jun 24, 2026)
All 10 items from FX_Trading_Tracker_User_Feedback.xlsx implemented and tested:

0. **Transaction Type → Buy/Sell**: Replaced Today/Tomorrow/Spot with Buy and Sell
1. **Counterparty Reference Entity**: New collection with CRUD in admin UI (Counterparties tab). Seeded: CLSC, PJ, Verite
2. **Source (From) → Counterparty**: For FX Local and FX-Intercompany, Company replaced with Counterparty dropdown
3. **Ours Counterparty Display**: Shows "Counterparty: {name}" in Ours section when applicable
4. **FX-Intercompany Transfer Type**: New transfer type seeded. Both Source and Destination show Counterparty
5. **Dynamic Ours Label**: Renamed to "Selling Counterparty Ours (Receiving Account)" for FX-Intercompany
6. **Buying Counterparty Ours**: New section with Bank/Account for FX-Intercompany deals. Backend model includes buying_ours_type/bank/account_num/wallet_address
7. **Settlement Dual Lines**: FX-Intercompany deals show .1 (Sell) and .2 (Buy) reference suffixes
8. **TMS Report (SAP)**: 21-column SAP mass upload format. Intercompany dual lines. CSV/JSON/PDF export
9. **Simplified Currency**: Single dropdown (removed Sell Currency). Formula = Amount × Rate only (removed divide logic)

Tested: 11/11 backend + 12/12 frontend (100%)

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services
- **P2**: TMS pagination fix for intercompany row expansion
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery
