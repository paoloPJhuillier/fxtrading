# FX Trading Tracker — PRD

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123
- **System Admin**: sysadmin@fxtracker.com / SysAdmin@123

## Architecture
- **Frontend**: React 19.0.0, React Router 7.5.1, TailwindCSS 3.4.17, Shadcn/UI
- **Backend**: FastAPI 0.110.1, Pydantic 2.12.5, reportlab 4.4.10
- **Database**: Switchable (DB_TYPE): MongoDB 7.0.31 | Couchbase Enterprise SDK 4.6.0
- **Storage**: Switchable (STORAGE_TYPE): Emergent Object Storage | S3-compatible (boto3 1.42.58)

## Roles
- **Trader**: Create deals, upload client proofs, view own deals, reports
- **Treasury**: Process deals (confirm/return), upload processor proofs, reports
- **Admin**: Manage users, reference data, audit trail, report permissions
- **System Admin (sysadmin)**: Everything admin can do + DB reset, DB export, DB stats

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

### System Administration (Complete - May 16, 2026)
- New **sysadmin** role (separate from admin), auto-seeded on startup
- **DB Stats**: GET /api/system/db-stats — record counts for all 11 collections
- **DB Export**: GET /api/system/export/{entity}?format=csv|json — export any collection
  - Entities: deals, audit_logs, users, companies, banks, bank_accounts, currencies, transaction_types, transfer_types
  - CSV excludes sensitive fields (password_hash, settlement_proofs, history)
  - JSON exports full data
- **DB Reset**: POST /api/system/db-reset — type-to-confirm "RESET DATABASE"
  - Wipes: deals, audit_logs, counters, report_permissions
  - Retains: users, companies, banks, bank_accounts, currencies, transaction_types, transfer_types
- sysadmin inherits all admin permissions (require_role check)
- Client-side route guard on /system (redirects non-sysadmin to dashboard)
- Tested: 18/18 backend + 6/6 frontend (100%)

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services
- **P1**: Extract shared deal formula to useDealFormulas hook (DRY)
- **P2**: Streaming response for large exports (OOM prevention)
- **P2**: Auto-backup before DB reset
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery
