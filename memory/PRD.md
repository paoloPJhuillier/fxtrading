# FX Trading Tracker — PRD

## Original Problem Statement
Build an FX Trading Tracker platform with secure role-based login, deal ticket management for traders, processing capabilities for treasury operations, and admin features for user management and audit trails. Prepare for on-premise deployment with switchable storage (Emergent / Huawei OBS / S3) and switchable database (MongoDB / Couchbase Enterprise).

## User Personas
- **Trader**: Creates and manages FX deal tickets
- **Treasury**: Processes deal tickets (confirm, return, cancel)
- **Admin**: Manages users, reference data, and views audit trails

---

## Technology Stack

### Runtime Environment
| Component | Version |
|-----------|---------|
| Node.js | 20.20.2 |
| Python | 3.11.15 |
| MongoDB | 7.0.31 |
| Couchbase Enterprise (Capella) | SDK 4.6.0 |

### Backend (Python / FastAPI)
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.110.1 | Web framework, REST API |
| uvicorn | 0.25.0 | ASGI server with hot-reload |
| starlette | 0.37.2 | ASGI toolkit (CORS, routing) |
| pydantic | 2.12.5 | Request/response validation |
| motor | 3.3.1 | Async MongoDB driver |
| pymongo | 4.5.0 | MongoDB synchronous operations (ReturnDocument) |
| couchbase | 4.6.0 | Couchbase Enterprise SDK (KV, N1QL, scopes/collections) |
| boto3 | 1.42.58 | S3-compatible object storage (Huawei OBS, MinIO) |
| python-jose | 3.5.0 | JWT token encode/decode |
| passlib | 1.7.4 | Password hashing framework |
| bcrypt | 4.1.3 | Bcrypt password hashing backend |
| reportlab | 4.4.10 | PDF report generation |
| python-dotenv | 1.2.1 | Environment variable loading |
| python-multipart | 0.0.22 | File upload handling |

### Frontend (React)
| Package | Version | Purpose |
|---------|---------|---------|
| react | 19.0.0 | UI framework |
| react-dom | 19.0.0 | DOM rendering |
| react-router-dom | 7.5.1 | Client-side routing |
| react-scripts | 5.0.1 | CRA build toolchain |
| @craco/craco | 7.1.0 | CRA config override (aliases) |
| axios | 1.8.4 | HTTP client with interceptors |
| tailwindcss | 3.4.17 | Utility-first CSS |
| tailwindcss-animate | 1.0.7 | Animation utilities |
| lucide-react | 0.507.0 | Icon library |
| sonner | 2.0.3 | Toast notifications |
| recharts | 3.6.0 | Dashboard charts |
| date-fns | 4.1.0 | Date formatting utilities |
| zod | 3.24.4 | Schema validation |
| react-hook-form | 7.56.2 | Form state management |
| react-day-picker | 8.10.1 | Date picker component |
| class-variance-authority | 0.7.1 | Component variant styling |
| clsx | 2.1.1 | Conditional classnames |
| tailwind-merge | 3.2.0 | Tailwind class conflict resolution |

### Shadcn/UI (Radix Primitives)
| Package | Version |
|---------|---------|
| @radix-ui/react-dialog | 1.1.11 |
| @radix-ui/react-select | 2.2.2 |
| @radix-ui/react-dropdown-menu | 2.1.12 |
| @radix-ui/react-tabs | 1.1.9 |
| @radix-ui/react-popover | 1.1.11 |
| @radix-ui/react-label | 2.1.4 |
| @radix-ui/react-checkbox | 1.2.3 |
| @radix-ui/react-scroll-area | 1.2.6 |
| @radix-ui/react-tooltip | 1.2.4 |
| @radix-ui/react-separator | 1.1.4 |
| @radix-ui/react-switch | 1.2.2 |
| @radix-ui/react-slot | 1.2.0 |
| @radix-ui/react-accordion | 1.2.8 |
| @radix-ui/react-progress | 1.1.4 |
| @radix-ui/react-avatar | 1.1.7 |
| @radix-ui/react-toast | 1.2.11 |
| @radix-ui/react-radio-group | 1.3.4 |
| @radix-ui/react-slider | 1.3.2 |
| @radix-ui/react-hover-card | 1.1.11 |
| @radix-ui/react-toggle | 1.1.6 |
| @radix-ui/react-toggle-group | 1.1.7 |
| @radix-ui/react-collapsible | 1.1.8 |
| @radix-ui/react-context-menu | 2.2.12 |
| @radix-ui/react-menubar | 1.1.12 |
| @radix-ui/react-navigation-menu | 1.2.10 |
| @radix-ui/react-alert-dialog | 1.1.11 |
| @radix-ui/react-aspect-ratio | 1.1.4 |

### Infrastructure & Deployment
| Component | Detail |
|-----------|--------|
| Hosting | Kubernetes container (Emergent Platform) |
| Reverse Proxy | Kubernetes Ingress (/api → port 8001, / → port 3000) |
| Process Manager | Supervisor (frontend + backend) |
| Object Storage (Dev) | Emergent Object Storage API |
| Object Storage (On-Prem) | S3-compatible via boto3 (Huawei OBS / MinIO) |
| Database (Dev) | MongoDB 7.0.31 (local) |
| Database (On-Prem) | Couchbase Enterprise (Capella, SDK 4.6.0) |

### Dev/Build Tools
| Tool | Version |
|------|---------|
| ESLint | 9.23.0 |
| PostCSS | 8.4.49 |
| Autoprefixer | 10.4.20 |

---

## Environment Variables

### Backend (`/app/backend/.env`)
| Variable | Purpose | Example |
|----------|---------|---------|
| MONGO_URL | MongoDB connection string | mongodb://localhost:27017 |
| DB_NAME | MongoDB database name | test_database |
| DB_TYPE | Database backend selector | mongodb \| couchbase |
| CB_CONNECTION_STRING | Couchbase cluster address | couchbases://cb.xxx.cloud.couchbase.com |
| CB_USERNAME | Couchbase auth user | fxtrading_app |
| CB_PASSWORD | Couchbase auth password | (secret) |
| CB_BUCKET_NAME | Couchbase bucket | db_fxtrading |
| JWT_SECRET | JWT signing key | (secret) |
| CORS_ORIGINS | Allowed CORS origins | * |
| EMERGENT_LLM_KEY | Emergent storage init key | sk-emergent-xxx |
| STORAGE_TYPE | Storage backend selector | emergent \| s3 |
| S3_ENDPOINT_URL | S3-compatible endpoint | http://localhost:9000 |
| S3_ACCESS_KEY_ID | S3 access key | minioadmin |
| S3_SECRET_ACCESS_KEY | S3 secret key | minioadmin |
| S3_BUCKET_NAME | S3 bucket name | fx-trading-tracker |
| S3_REGION | S3 region | us-east-1 |

### Frontend (`/app/frontend/.env`)
| Variable | Purpose |
|----------|---------|
| REACT_APP_BACKEND_URL | API base URL for all requests |

---

## Couchbase Scope/Collection Mapping
| Scope | Collection | MongoDB Equivalent |
|-------|-----------|-------------------|
| identity | users | users |
| trading | deals | deals |
| trading | deal_counters | counters |
| reference | companies | companies |
| reference | banks | banks |
| reference | bank_accounts | bank_accounts |
| reference | currencies | currencies |
| reference | transaction_types | transaction_types |
| reference | transfer_types | transfer_types |
| audit | audit_logs | audit_logs |

---

## Credentials
- Trader: trader@fxtracker.com / Trader@123
- Treasury: treasury@fxtracker.com / Treasury@123
- Admin: admin@fxtracker.com / Admin@123

---

## Key Files
- `backend/server.py` — All API endpoints (~1260 lines)
- `backend/services/database.py` — Database factory, SCOPE_MAP, get_database()
- `backend/services/db_mongo.py` — MongoDB backend (MongoDatabase, MongoCollection, MongoCursor)
- `backend/services/db_couchbase.py` — Couchbase backend (CouchbaseDatabase, N1QL translation, KV ops)
- `backend/services/storage.py` — Storage abstraction (EmergentStorage, S3Storage)
- `backend/services/reports.py` — Report generation engine (CSV + PDF via reportlab)
- `frontend/src/pages/ReportsPage.jsx` — Reports UI (selector + table viewer + export)
- `frontend/src/pages/NewDealPage.jsx` — Create new deal
- `frontend/src/pages/EditDealPage.jsx` — Edit returned deal
- `frontend/src/pages/DealsPage.jsx` — Trader deal list + detail dialog
- `frontend/src/pages/TreasuryPage.jsx` — Treasury deal queue
- `frontend/src/pages/ReferenceDataPage.jsx` — Admin reference data + bank accounts
- `frontend/src/components/DealFormFields.jsx` — Shared form components (SearchSelect, BankAccountSelect)
- `frontend/src/components/Layout.jsx` — Sidebar nav, role-based menu
- `frontend/src/lib/api.js` — Axios instance with JWT interceptor
- `frontend/src/lib/auth.js` — AuthContext, login/logout, localStorage persistence
- `frontend/src/App.js` — Routes, lazy loading, prefetch

---

## What's Been Implemented

### Core Platform (Complete)
- Full auth with JWT, deal CRUD, dashboard, treasury queue, admin pages, file upload

### Performance Optimizations (Complete)
- AbortController, lazy loading, deferred rendering, component memoization

### Bank Account Management (Complete - Mar 17, 2026)
### Deal History Timeline (Complete - Mar 17, 2026)
### Split Settlement Proofs (Complete - Mar 17, 2026)
### Returned Deal Edit Page (Complete - Mar 17, 2026)
### Switchable Storage Abstraction (Complete - Apr 24, 2026)
### Switchable Database Abstraction (Complete - Apr 24, 2026)

### Reports Feature (Complete - Apr 27, 2026)
- 7 industry-standard FX trading reports with tabular data view + export
- Report selector page → click → full data table with filters + CSV/PDF export
- Deal Blotter, Settlement, Open Positions, Audit Trail (admin), User Activity (admin), Volume Summary, Client Activity
- Sortable columns, filter bar, status badges, alternating rows
- PDF branding: Primary #08263e/#ec474e, Secondary #518dca/#f1f2f2
- Backend: 30/30 tests passed, Frontend: 100% pass

---

## Backlog / Future Tasks
- **P1**: Backend refactoring — split server.py into /routes, /models, /services modules
- **P2**: Email notifications for deal status changes
- **P2**: Scheduled report delivery (auto-email daily/weekly reports)
