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

## What's Been Implemented

### Core Platform
- Multi-role auth (Trader, Treasury, Admin, Sysadmin)
- Deal lifecycle: create → pending → confirm/return/cancel
- Settlement proof upload (client + processor)
- Returned deal edit & resubmit
- Switchable Storage (Emergent ↔ S3/Huawei OBS) and Database (MongoDB ↔ Couchbase)
- 8 Reports with server-side pagination, autocomplete filters, CSV/PDF export
- Admin report permissions, System Admin page (DB stats/export/reset)
- FX Assessment 9 Revisions

### User Feedback 10 Items (Jun 24, 2026)
- Buy/Sell transaction types, Counterparty entity, FX-Intercompany, TMS Report, Simplified currency

### 12-Item Feedback Fixes (Aug 3, 2026)
1. FX Client tab label, 2. Add FX Client dialog, 3. USDC→USD Circle
4. Treasury Last Action column, 5-6. currency_amount display
7. Account Name required, 8. Searchable bank account selector
9. Bank account CSV/Excel import, 10. FX Client CSV/Excel import
11. FX - Corporate Settlement transfer type, 12. Crypto networks (SOLANA/ETHEREUM/TRON)

### Bank Account Import Enhancement (Aug 3, 2026)
- **Legacy fld_* format support**: Auto-detects `fld_AccountNo`, `fld_BranchAddress`, `fld_BankCode`, `fld_CurrencyCode`, `fld_AccountType`, etc.
- **Global multi-bank import**: POST /api/reference/bank-accounts/import — matches `fld_BankCode` to existing banks, auto-creates new banks if not found
- **Rich account fields**: Persists `currency_code`, `account_type`, `bank_address`, `contact_no`, `account_alias` when available
- **UI**: "Import Accounts CSV" button on Banks tab for global import; "Import" button in per-bank dialog
- **Accounts table**: Now shows Currency and Type columns
- Tested: 1,689 accounts imported across 31 auto-created banks from production CSV (1,985 rows)

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services
- **P2**: TMS pagination fix for intercompany row expansion
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery (daily/weekly)
- **P2**: Reports aggregation scalability (native DB pipelines)
- **P2**: Approval workflow for TMS
