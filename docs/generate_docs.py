"""
Generate comprehensive FX Trading Tracker documentation in PDF and DOCX.
Outputs to /app/docs/
"""

import os
import io
from datetime import datetime, timezone

# ── PDF generation via reportlab ─────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)

# ── DOCX generation via python-docx ──────────────────────────────────────────
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT

# Brand colors
C_NAVY = colors.HexColor("#08263e")
C_RED = colors.HexColor("#ec474e")
C_BLUE = colors.HexColor("#518dca")
C_GRAY = colors.HexColor("#f1f2f2")

NAVY_RGB = RGBColor(0x08, 0x26, 0x3e)
RED_RGB = RGBColor(0xec, 0x47, 0x4e)
BLUE_RGB = RGBColor(0x51, 0x8d, 0xca)

OUT_DIR = "/app/docs"
GENERATED = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  CONTENT DATA                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

TECH_STACK_BACKEND = [
    ("fastapi", "0.110.1", "Web framework, REST API"),
    ("uvicorn", "0.25.0", "ASGI server with hot-reload"),
    ("starlette", "0.37.2", "ASGI toolkit (CORS, routing)"),
    ("pydantic", "2.12.5", "Request/response validation, data models"),
    ("motor", "3.3.1", "Async MongoDB driver"),
    ("pymongo", "4.5.0", "MongoDB synchronous operations"),
    ("couchbase", "4.6.0", "Couchbase Enterprise SDK (KV, N1QL, scopes/collections)"),
    ("boto3", "1.42.58", "S3-compatible object storage (Huawei OBS, MinIO, AWS)"),
    ("python-jose", "3.5.0", "JWT token encode/decode (HS256)"),
    ("passlib", "1.7.4", "Password hashing framework"),
    ("bcrypt", "4.1.3", "Bcrypt password hashing backend"),
    ("reportlab", "4.4.10", "PDF report generation with branded layout"),
    ("python-dotenv", "1.2.1", "Environment variable loading from .env"),
    ("python-multipart", "0.0.22", "Multipart file upload handling"),
]

TECH_STACK_FRONTEND = [
    ("react", "19.0.0", "UI framework"),
    ("react-dom", "19.0.0", "DOM rendering"),
    ("react-router-dom", "7.5.1", "Client-side routing with lazy loading"),
    ("axios", "1.8.4", "HTTP client with JWT interceptor"),
    ("tailwindcss", "3.4.17", "Utility-first CSS framework"),
    ("lucide-react", "0.507.0", "Icon library (200+ icons)"),
    ("sonner", "2.0.3", "Toast notifications"),
    ("recharts", "3.6.0", "Dashboard charts and data visualization"),
    ("date-fns", "4.1.0", "Date formatting and manipulation"),
    ("zod", "3.24.4", "Schema validation"),
    ("react-hook-form", "7.56.2", "Form state management"),
    ("react-day-picker", "8.10.1", "Date picker component"),
    ("@craco/craco", "7.1.0", "CRA config override (path aliases)"),
    ("class-variance-authority", "0.7.1", "Component variant styling"),
    ("clsx", "2.1.1", "Conditional CSS classnames"),
    ("tailwind-merge", "3.2.0", "Tailwind class conflict resolution"),
]

RADIX_COMPONENTS = [
    ("@radix-ui/react-dialog", "1.1.11"),
    ("@radix-ui/react-select", "2.2.2"),
    ("@radix-ui/react-dropdown-menu", "2.1.12"),
    ("@radix-ui/react-tabs", "1.1.9"),
    ("@radix-ui/react-popover", "1.1.11"),
    ("@radix-ui/react-label", "2.1.4"),
    ("@radix-ui/react-checkbox", "1.2.3"),
    ("@radix-ui/react-scroll-area", "1.2.6"),
    ("@radix-ui/react-tooltip", "1.2.4"),
    ("@radix-ui/react-separator", "1.1.4"),
    ("@radix-ui/react-switch", "1.2.2"),
    ("@radix-ui/react-slot", "1.2.0"),
    ("@radix-ui/react-accordion", "1.2.8"),
    ("@radix-ui/react-avatar", "1.1.7"),
    ("@radix-ui/react-toast", "1.2.11"),
    ("@radix-ui/react-progress", "1.1.4"),
    ("@radix-ui/react-radio-group", "1.3.4"),
    ("@radix-ui/react-alert-dialog", "1.1.11"),
    ("@radix-ui/react-hover-card", "1.1.11"),
    ("@radix-ui/react-collapsible", "1.1.8"),
    ("@radix-ui/react-context-menu", "2.2.12"),
    ("@radix-ui/react-menubar", "1.1.12"),
    ("@radix-ui/react-navigation-menu", "1.2.10"),
    ("@radix-ui/react-slider", "1.3.2"),
    ("@radix-ui/react-toggle", "1.1.6"),
    ("@radix-ui/react-toggle-group", "1.1.7"),
    ("@radix-ui/react-aspect-ratio", "1.1.4"),
]

RUNTIME = [
    ("Node.js", "20.20.2"),
    ("Python", "3.11.15"),
    ("MongoDB", "7.0.31"),
    ("Couchbase Enterprise SDK", "4.6.0"),
]

ENV_VARS = [
    ("MONGO_URL", "MongoDB connection string", "mongodb://localhost:27017"),
    ("DB_NAME", "MongoDB database name", "test_database"),
    ("DB_TYPE", "Database backend selector", "mongodb | couchbase"),
    ("CB_CONNECTION_STRING", "Couchbase cluster address", "couchbases://cb.xxx.cloud.couchbase.com"),
    ("CB_USERNAME", "Couchbase auth username", "fxtrading_app"),
    ("CB_PASSWORD", "Couchbase auth password", "(secret)"),
    ("CB_BUCKET_NAME", "Couchbase bucket name", "db_fxtrading"),
    ("JWT_SECRET", "JWT signing key", "(secret)"),
    ("CORS_ORIGINS", "Allowed CORS origins", "*"),
    ("EMERGENT_LLM_KEY", "Emergent storage init key", "sk-emergent-xxx"),
    ("STORAGE_TYPE", "Storage backend selector", "emergent | s3"),
    ("S3_ENDPOINT_URL", "S3-compatible endpoint URL", "http://localhost:9000"),
    ("S3_ACCESS_KEY_ID", "S3 access key ID", "minioadmin"),
    ("S3_SECRET_ACCESS_KEY", "S3 secret access key", "(secret)"),
    ("S3_BUCKET_NAME", "S3 bucket name", "fx-trading-tracker"),
    ("S3_REGION", "S3 region identifier", "us-east-1"),
]

SCOPE_MAP = [
    ("identity", "users", "users", "User accounts, credentials, roles (trader, treasury, admin, sysadmin)"),
    ("trading", "deals", "deals", "FX deal tickets with full lifecycle, counterparty, crypto networks"),
    ("trading", "deal_counters", "counters", "Sequential deal reference counters"),
    ("reference", "companies", "companies", "FX Client/company entities"),
    ("reference", "banks", "banks", "Banking institutions with SWIFT codes"),
    ("reference", "bank_accounts", "bank_accounts", "Bank accounts with name, number, currency, type, address"),
    ("reference", "currencies", "currencies", "Fiat (31), stablecoin (16), and crypto (18) currencies"),
    ("reference", "transaction_types", "transaction_types", "Buy, Sell"),
    ("reference", "transfer_types", "transfer_types", "FX Crypto, FX Local, PDAX WD, FX Bank Deal, FX-Intercompany, FX - Corporate Settlement"),
    ("reference", "counterparties", "counterparties", "PJL Group entities (CLSC, PJ, Verite, etc.)"),
    ("reference", "report_permissions", "report_permissions", "Per-role report access toggles"),
    ("audit", "audit_logs", "audit_logs", "Full audit trail of all actions"),
]

API_ENDPOINTS = [
    # Auth
    ("POST", "/api/auth/login", "All", "Authenticate and receive JWT token"),
    ("GET", "/api/auth/me", "All", "Get current user profile"),
    ("PUT", "/api/auth/change-password", "All", "Change own password"),
    # Users
    ("GET", "/api/users", "Admin", "List users with search and pagination"),
    ("POST", "/api/users", "Admin", "Create new user account"),
    ("PUT", "/api/users/{user_id}", "Admin", "Update user details"),
    ("DELETE", "/api/users/{user_id}", "Admin", "Delete user account"),
    # Deals
    ("GET", "/api/deals", "Trader/Treasury/Admin", "List deals with filters and pagination"),
    ("POST", "/api/deals", "Trader", "Create new deal ticket"),
    ("GET", "/api/deals/{deal_id}", "Trader/Treasury/Admin", "Get deal detail with history and proofs"),
    ("PUT", "/api/deals/{deal_id}/process", "Treasury", "Confirm or return a pending deal"),
    ("PUT", "/api/deals/{deal_id}/cancel", "Trader", "Cancel own pending deal"),
    ("PUT", "/api/deals/{deal_id}/resubmit", "Trader", "Resubmit a returned deal"),
    ("PUT", "/api/deals/{deal_id}/edit", "Trader", "Edit a returned deal's fields"),
    ("GET", "/api/deals/export", "Trader/Treasury/Admin", "Export deals as CSV"),
    # Files
    ("POST", "/api/deals/{deal_id}/upload", "All", "Upload settlement proof (image/PDF, max 10MB)"),
    ("GET", "/api/files/{path}", "Public", "Download uploaded file by storage path"),
    ("DELETE", "/api/deals/{deal_id}/proofs/{proof_id}", "All", "Delete settlement proof"),
    # Reference Data
    ("GET", "/api/reference/{entity_type}", "All", "List reference items (companies, banks, currencies, counterparties, etc.)"),
    ("POST", "/api/reference/{entity_type}", "Admin", "Create reference item"),
    ("PUT", "/api/reference/{entity_type}/{item_id}", "Admin", "Update reference item"),
    ("DELETE", "/api/reference/{entity_type}/{item_id}", "Admin", "Delete reference item"),
    # Bank Accounts
    ("GET", "/api/reference/banks/{bank_id}/accounts", "All", "List bank accounts for a bank"),
    ("POST", "/api/reference/banks/{bank_id}/accounts", "All", "Add bank account (account_name required)"),
    ("PUT", "/api/reference/banks/{bank_id}/accounts/{id}", "Admin", "Update bank account"),
    ("DELETE", "/api/reference/banks/{bank_id}/accounts/{id}", "Admin", "Delete bank account"),
    # Bulk Import
    ("POST", "/api/reference/banks/{bank_id}/accounts/import", "Admin", "Import bank accounts CSV/Excel (per-bank)"),
    ("POST", "/api/reference/bank-accounts/import", "Admin", "Global multi-bank import (fld_* format supported)"),
    ("POST", "/api/reference/companies/import", "Admin", "Import FX Clients CSV/Excel"),
    # Dashboard & Audit
    ("GET", "/api/dashboard/stats", "All", "Dashboard statistics and aggregation"),
    ("GET", "/api/audit-logs", "Admin", "Audit trail with filters and pagination"),
    # Reports
    ("GET", "/api/reports/deal-blotter", "All", "Deal Blotter (format=json|csv|pdf, paginated)"),
    ("GET", "/api/reports/settlement", "All", "Settlement Report (format=json|csv|pdf, paginated)"),
    ("GET", "/api/reports/open-positions", "All", "Open Positions (format=json|csv|pdf)"),
    ("GET", "/api/reports/audit-trail", "Admin", "Audit Trail Report (format=json|csv|pdf, paginated)"),
    ("GET", "/api/reports/user-activity", "Admin", "User Activity Report (format=json|csv|pdf)"),
    ("GET", "/api/reports/volume-summary", "All", "Volume Summary (format=json|csv|pdf, group_by)"),
    ("GET", "/api/reports/client-activity", "All", "Client Activity Report (format=json|csv|pdf)"),
    ("GET", "/api/reports/tms", "All", "TMS/SAP Report — 21-column mass upload format"),
    ("GET/PUT", "/api/reports/permissions", "Admin", "Manage role-based report permissions"),
    # System
    ("GET", "/api/storage/status", "Admin", "Storage backend status and config"),
    ("GET", "/api/database/status", "Admin", "Database backend status and config"),
    ("GET", "/api/system/stats", "Sysadmin", "Database collection counts"),
    ("GET", "/api/system/export/{collection}", "Sysadmin", "Export collection as CSV or JSON"),
    ("POST", "/api/system/reset", "Sysadmin", "Controlled database reset (retains users/ref data)"),
    # Documentation
    ("GET", "/api/documentation/list", "All", "List available documentation files"),
    ("GET", "/api/documentation/download/{filename}", "All", "Download single doc file"),
    ("GET", "/api/documentation/download-all", "All", "Download all docs as ZIP archive"),
]

DATA_MODELS = [
    ("users", [
        ("id", "string (UUID)", "Unique identifier"),
        ("email", "string", "Login email (unique)"),
        ("first_name", "string", "First name"),
        ("last_name", "string", "Last name"),
        ("password_hash", "string", "Bcrypt hashed password"),
        ("role", "string", "admin | trader | treasury | sysadmin"),
        ("is_active", "boolean", "Account enabled flag"),
        ("created_at", "string (ISO 8601)", "Creation timestamp"),
    ]),
    ("deals", [
        ("id", "string (UUID)", "Unique identifier"),
        ("reference_number", "string", "Sequential ref (FX-YYYYMMDD-NNNN)"),
        ("transaction_type", "string", "Buy | Sell"),
        ("transfer_type", "string", "FX Crypto | FX Local | PDAX WD | FX Bank Deal | FX-Intercompany | FX - Corporate Settlement"),
        ("deal_date", "string (YYYY-MM-DD)", "Deal execution date"),
        ("value_date", "string (YYYY-MM-DD)", "Settlement value date"),
        ("client_name", "string", "Client/counterparty name"),
        ("counterparty", "string", "PJL Group entity (FX Local/Intercompany/Corp Settlement)"),
        ("from_type / to_type / ours_type", "string", "bank | crypto"),
        ("from_company / to_company", "string", "Company name"),
        ("from_bank / to_bank / ours_bank", "string", "Bank name"),
        ("from_account_num / to_account_num / ours_account_num", "string", "Account number"),
        ("from_wallet_address / to_wallet_address / ours_wallet_address", "string", "Crypto wallet"),
        ("from_network / to_network / ours_network", "string", "Crypto network: SOLANA | ETHEREUM | TRON"),
        ("buying_ours_type / buying_ours_bank / buying_ours_account_num", "string", "Buying Counterparty Ours (FX-Intercompany)"),
        ("buying_ours_wallet_address / buying_ours_network", "string", "Buying Counterparty crypto (FX-Intercompany)"),
        ("buy_currency", "string", "Currency code"),
        ("sell_currency", "string", "Optional sell currency"),
        ("currency_amount", "float", "Principal/original amount"),
        ("amount", "float", "Converted amount (currency_amount x rate)"),
        ("rate", "float", "Exchange rate"),
        ("status", "string", "pending | confirmed | returned | cancelled"),
        ("remarks", "string", "Trader remarks"),
        ("treasury_remarks", "string", "Treasury processing notes"),
        ("settlement_proofs", "array", "Array of proof objects {id, path, filename, proof_type}"),
        ("history", "array", "Array of history entries {action, user_name, changes, timestamp}"),
        ("created_by / created_by_name", "string", "Creator user ID and name"),
        ("processed_by / processed_by_name", "string", "Treasury processor ID and name"),
        ("created_at / updated_at", "string (ISO 8601)", "Timestamps"),
    ]),
    ("bank_accounts", [
        ("id", "string (UUID)", "Unique identifier"),
        ("bank_id", "string (UUID)", "Foreign key to bank"),
        ("account_number", "string", "Bank account number"),
        ("account_name", "string", "Account descriptive name (required)"),
        ("currency_code", "string", "PHP, USD, etc. (from import)"),
        ("account_type", "string", "SA, CA, etc. (from import)"),
        ("bank_address", "string", "Branch address (from import)"),
        ("contact_no", "string", "Contact number (from import)"),
        ("account_alias", "string", "Short alias (from import)"),
        ("is_active", "boolean", "Account enabled flag"),
        ("created_at", "string (ISO 8601)", "Creation timestamp"),
    ]),
    ("audit_logs", [
        ("id", "string (UUID)", "Unique identifier"),
        ("action", "string", "Action type (deal_created, deal_confirmed, etc.)"),
        ("entity_type", "string", "Entity type (deal, user, bank_account)"),
        ("entity_id", "string", "Entity UUID"),
        ("entity_ref", "string", "Human-readable reference"),
        ("user_id / user_name / user_role", "string", "Acting user details"),
        ("details", "string", "Human-readable description"),
        ("metadata", "object", "Additional structured data"),
        ("created_at", "string (ISO 8601)", "Action timestamp"),
    ]),
]

REPORTS = [
    ("Deal Blotter", "Complete log of all executed deals", "Date range, status, client, currency", "All roles"),
    ("Settlement Report", "Deals grouped by value date with bank details and proof status; FX-Intercompany dual lines (.1/.2)", "Date range, from/to bank", "All roles"),
    ("Open Positions", "Pending deals grouped by currency pair showing net buy/sell exposure", "None (current snapshot)", "All roles"),
    ("Transaction Audit Trail", "Full history of every deal action with timestamps and change logs", "Date range, user", "Admin only"),
    ("User Activity", "Per-user breakdown of deals created, processed, returned, proofs uploaded", "Date range", "Admin only"),
    ("Volume Summary", "Deal counts and volumes grouped by day, week, or month", "Date range, group by", "All roles"),
    ("Client Activity", "Per-client deal volume, frequency, average deal size, currency pairs", "Date range, client", "All roles"),
    ("TMS Report (SAP)", "21-column SAP mass upload format; FX-Intercompany generates .1 (Sell) + .2 (Buy) rows", "Date range", "All roles"),
]

BUSINESS_RULES = [
    ("Transaction Types", [
        "Two transaction types: Buy and Sell",
        "Transaction type is selected via dropdown in the deal form",
    ]),
    ("Transfer Types and Conditional Form Logic", [
        "6 transfer types: FX Crypto Conversion, FX Local, PDAX Withdrawal, FX Bank Deal, FX-Intercompany, FX - Corporate Settlement",
        "FX Bank Deal: Destination (To) section is hidden; server clears to_* fields; client proof upload blocked",
        "FX Local and FX - Corporate Settlement: Source/Destination show Counterparty dropdown instead of Company",
        "FX-Intercompany: Both Source and Destination show Counterparty; dual Ours sections (Selling Counterparty Ours + Buying Counterparty Ours)",
    ]),
    ("Counterparty Management", [
        "Counterparties are PJL Group entities (e.g., CLSC, PJ, Verite) managed in Admin Reference Data",
        "Counterparty field appears for FX Local, FX - Corporate Settlement, and FX-Intercompany transfer types",
        "Counterparty represents the PJL Group entity for the deal, not a separate independent party",
    ]),
    ("Crypto Network Selection", [
        "When any account section (Source, Destination, Ours) is set to Crypto mode, a Network dropdown is required",
        "Available networks: SOLANA, ETHEREUM, TRON",
        "Network is persisted as from_network, to_network, ours_network, buying_ours_network",
    ]),
    ("Currency and Amount Handling", [
        "Single currency dropdown (Buy Currency) with searchable autocomplete",
        "Converted Amount = Currency Amount x Exchange Rate",
        "Amount fields display with locale-aware comma formatting",
        "Tables show currency_amount (original principal) with currency label instead of converted amount",
    ]),
    ("Settlement Proof Access Control", [
        "Client Settlement Proofs: only Traders can upload (Treasury can view only)",
        "Processor Settlement Proofs: Treasury can upload",
        "Both proof types: all roles can view and download",
        "Treasury cannot confirm a deal if zero settlement proofs are attached (UI + server enforced)",
        "Client proofs are not applicable for FX Bank Deal transactions",
    ]),
    ("Bank Account Management", [
        "Account Name is required when creating bank accounts",
        "Bank account selectors show searchable autocomplete with account name + account number",
        "CSV/Excel import supported per-bank and globally (multi-bank with auto bank creation)",
        "Legacy fld_* format auto-detected: fld_AccountNo, fld_BranchAddress, fld_BankCode, fld_CurrencyCode, fld_AccountType",
        "Extended fields persisted: currency_code, account_type, bank_address, contact_no, account_alias",
    ]),
    ("FX-Intercompany Dual-Line Handling", [
        "FX-Intercompany deals generate dual settlement/TMS lines: .1 (Sell side) and .2 (Buy side)",
        "Each line has its own counterparty ours account details",
        "Both lines appear in Settlement Report and TMS Report",
    ]),
    ("Deal History and Last Action", [
        "All deal mutations recorded in history array (created, confirmed, returned, cancelled, edited, resubmitted, proof uploaded/deleted)",
        "My Deals and Treasury Queue tables show Last Action column with colored badges",
        "List API truncates history to last 3 entries for performance; detail API returns full history",
    ]),
    ("System Administration", [
        "Sysadmin role: full admin access + database stats, collection exports, controlled reset",
        "Database reset clears deals, audit logs, counters, report permissions",
        "Database reset retains users, reference data, and bank accounts",
    ]),
]


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PDF BUILDER                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _pdf_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("DocTitle", parent=ss["Title"], fontSize=22, textColor=C_NAVY, spaceAfter=6, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("DocSub", parent=ss["Normal"], fontSize=10, textColor=C_BLUE, spaceAfter=20))
    ss.add(ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, textColor=C_NAVY, spaceBefore=20, spaceAfter=8, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, textColor=C_NAVY, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("H3", parent=ss["Heading3"], fontSize=10, textColor=C_BLUE, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=9, leading=13, alignment=TA_JUSTIFY))
    ss.add(ParagraphStyle("BodySmall", parent=ss["Normal"], fontSize=8, leading=11))
    ss.add(ParagraphStyle("BulletText", parent=ss["Normal"], fontSize=9, leading=12, leftIndent=15, bulletIndent=0))
    ss.add(ParagraphStyle("CellText", parent=ss["Normal"], fontSize=7, leading=9))
    ss.add(ParagraphStyle("TOCEntry", parent=ss["Normal"], fontSize=10, leading=18, textColor=C_NAVY))
    return ss


def _tbl_style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 6.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])


def _page_header(canvas, doc, title):
    canvas.saveState()
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, doc.pagesize[1] - 10*mm, doc.pagesize[0], 10*mm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(12*mm, doc.pagesize[1] - 7*mm, f"FX Trading Tracker  |  {title}")
    canvas.setFont("Helvetica", 6)
    canvas.drawRightString(doc.pagesize[0] - 12*mm, doc.pagesize[1] - 7*mm, GENERATED)
    canvas.setStrokeColor(C_RED)
    canvas.setLineWidth(1.2)
    canvas.line(0, doc.pagesize[1] - 10*mm, doc.pagesize[0], doc.pagesize[1] - 10*mm)
    canvas.setFillColor(C_NAVY)
    canvas.setFont("Helvetica", 6)
    canvas.drawRightString(doc.pagesize[0] - 12*mm, 7*mm, f"Page {doc.page}")
    canvas.drawString(12*mm, 7*mm, "CONFIDENTIAL")
    canvas.restoreState()


def build_pdf(filename, title, subtitle, sections_fn):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16*mm, bottomMargin=14*mm, leftMargin=14*mm, rightMargin=14*mm)
    ss = _pdf_styles()
    elems = []

    # Title page
    elems.append(Spacer(1, 60))
    elems.append(Paragraph(title, ss["DocTitle"]))
    elems.append(Paragraph(subtitle, ss["DocSub"]))
    elems.append(Spacer(1, 10))
    elems.append(Paragraph(f"Generated: {GENERATED}", ss["BodySmall"]))
    elems.append(Paragraph("Classification: CONFIDENTIAL", ss["BodySmall"]))
    elems.append(PageBreak())

    sections_fn(elems, ss)

    def on_page(c, d):
        _page_header(c, d, title)

    doc.build(elems, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(buf.read())
    print(f"  PDF: {path}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DOCX BUILDER                                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def _docx_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    # Header
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.size = Pt(8)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        from docx.oxml.ns import qn
        shading = cell._element.get_or_add_tcPr()
        sh_el = shading.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): "08263e"})
        shading.append(sh_el)
    # Rows
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(7.5)
            if ri % 2 == 1:
                from docx.oxml.ns import qn
                shading = cell._element.get_or_add_tcPr()
                sh_el = shading.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): "f1f2f2"})
                shading.append(sh_el)
    return table


def _docx_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = NAVY_RGB
    return h


def build_docx(filename, title, subtitle, sections_fn):
    doc = Document()
    # Margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    # Title
    t = doc.add_heading(title, 0)
    for run in t.runs:
        run.font.color.rgb = NAVY_RGB
    sub = doc.add_paragraph(subtitle)
    for run in sub.runs:
        run.font.color.rgb = BLUE_RGB
        run.font.size = Pt(11)
    doc.add_paragraph(f"Generated: {GENERATED}\nClassification: CONFIDENTIAL").runs[0].font.size = Pt(8)
    doc.add_page_break()

    sections_fn(doc)

    path = os.path.join(OUT_DIR, filename)
    doc.save(path)
    print(f"  DOCX: {path}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DOCUMENT 1: Technical Design Document                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def tdd_pdf_sections(elems, ss):
    def h1(t): elems.append(Paragraph(t, ss["H1"]))
    def h2(t): elems.append(Paragraph(t, ss["H2"]))
    def h3(t): elems.append(Paragraph(t, ss["H3"]))
    def body(t): elems.append(Paragraph(t, ss["Body"]))
    def sp(n=6): elems.append(Spacer(1, n))
    def tbl(headers, rows, widths=None):
        data = [headers] + rows
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(_tbl_style())
        elems.append(t)
        sp()

    # 1. Overview
    h1("1. System Overview")
    body("The FX Trading Tracker is a full-stack web application for managing foreign exchange deal tickets. It supports a three-role workflow: Traders create deal tickets, Treasury processes them (confirm/return), and Admins manage users, reference data, and audit trails. The platform is designed for on-premise deployment with switchable storage and database backends.")
    sp()

    # 2. Architecture
    h1("2. System Architecture")
    h2("2.1 High-Level Architecture")
    body("The application follows a client-server architecture with a React single-page application (SPA) frontend communicating with a FastAPI REST backend via JSON over HTTPS. All API routes are prefixed with /api and routed through a Kubernetes Ingress controller.")
    sp()
    tbl(["Layer", "Technology", "Version", "Description"],
        [["Frontend", "React SPA", "19.0.0", "Single-page app with lazy loading and route-based code splitting"],
         ["API Server", "FastAPI", "0.110.1", "Async REST API with Pydantic validation"],
         ["ASGI Server", "Uvicorn", "0.25.0", "Production ASGI server with hot-reload in dev"],
         ["Database (Dev)", "MongoDB", "7.0.31", "Document database via motor async driver"],
         ["Database (Prod)", "Couchbase Enterprise", "SDK 4.6.0", "Distributed NoSQL with scopes/collections"],
         ["Storage (Dev)", "Emergent Object Storage", "API v1", "Cloud-based file storage"],
         ["Storage (Prod)", "S3-Compatible (Huawei OBS)", "boto3 1.42.58", "On-premise object storage"],
         ["Process Manager", "Supervisor", "-", "Manages frontend (port 3000) and backend (port 8001)"]],
        widths=[70, 80, 55, 260])

    h2("2.2 Runtime Environment")
    tbl(["Component", "Version"],
        [[r[0], r[1]] for r in RUNTIME],
        widths=[150, 150])

    # 3. Backend Tech Stack
    h1("3. Backend Technology Stack")
    tbl(["Package", "Version", "Purpose"],
        [[p[0], p[1], p[2]] for p in TECH_STACK_BACKEND],
        widths=[90, 55, 320])

    # 4. Frontend Tech Stack
    h1("4. Frontend Technology Stack")
    h2("4.1 Core Dependencies")
    tbl(["Package", "Version", "Purpose"],
        [[p[0], p[1], p[2]] for p in TECH_STACK_FRONTEND],
        widths=[110, 50, 305])

    elems.append(PageBreak())
    h2("4.2 Shadcn/UI (Radix Primitives)")
    body("The UI component library is built on Radix UI primitives with Tailwind CSS styling (Shadcn pattern). All components are located in /app/frontend/src/components/ui/.")
    sp()
    half = len(RADIX_COMPONENTS) // 2 + 1
    tbl(["Package", "Version"],
        [[p[0], p[1]] for p in RADIX_COMPONENTS[:half]],
        widths=[200, 80])
    tbl(["Package", "Version"],
        [[p[0], p[1]] for p in RADIX_COMPONENTS[half:]],
        widths=[200, 80])

    # 5. Database Design
    elems.append(PageBreak())
    h1("5. Database Design")
    h2("5.1 Switchable Backend")
    body("The database layer is abstracted behind a factory pattern (services/database.py). The DB_TYPE environment variable controls which backend is active. Both backends expose identical MongoDB-like APIs (find, insert, update, delete, aggregate) to the application layer.")
    sp()
    h2("5.2 Couchbase Scope/Collection Mapping")
    body("Following Couchbase best practices, data is organized into logical scopes with separate collections. Primary and secondary indexes are auto-created on first startup.")
    sp()
    tbl(["Scope", "Collection", "MongoDB Equivalent", "Description"],
        [[s[0], s[1], s[2], s[3]] for s in SCOPE_MAP],
        widths=[60, 85, 85, 235])

    h2("5.3 Data Models")
    for model_name, fields in DATA_MODELS:
        h3(f"Collection: {model_name}")
        tbl(["Field", "Type", "Description"],
            [[f[0], f[1], f[2]] for f in fields],
            widths=[130, 85, 250])

    # 6. Storage Abstraction
    elems.append(PageBreak())
    h1("6. Storage Abstraction Layer")
    body("File storage (settlement proofs) is abstracted via services/storage.py with two implementations:")
    sp()
    tbl(["Backend", "Class", "Protocol", "Use Case"],
        [["emergent", "EmergentStorage", "Emergent Object Storage REST API", "Cloud dev environment"],
         ["s3", "S3Storage", "S3 API via boto3 (s3v4 signature, path-style)", "On-premise (Huawei OBS, MinIO, AWS)"]],
        widths=[55, 85, 175, 150])

    # 7. Environment Variables
    h1("7. Environment Variables")
    tbl(["Variable", "Purpose", "Example"],
        [[e[0], e[1], e[2]] for e in ENV_VARS],
        widths=[100, 170, 195])

    # 8. API Reference
    elems.append(PageBreak())
    h1("8. API Endpoint Reference")
    body("All endpoints are prefixed with /api. Authentication is via Bearer JWT token in the Authorization header. Token expiry: 24 hours.")
    sp()
    tbl(["Method", "Endpoint", "Access", "Description"],
        [[e[0], e[1], e[2], e[3]] for e in API_ENDPOINTS],
        widths=[35, 160, 85, 185])

    # 9. Reports
    elems.append(PageBreak())
    h1("9. Reports System")
    body("Seven industry-standard FX trading reports are available via the /reports page. Each report supports three output formats: JSON (for table preview), CSV (download), and PDF (branded download with company colors).")
    sp()
    tbl(["Report", "Description", "Filters", "Access"],
        [[r[0], r[1], r[2], r[3]] for r in REPORTS],
        widths=[80, 175, 100, 60])
    sp()
    h2("9.1 PDF Branding")
    tbl(["Element", "Color", "Hex"],
        [["Header bar / headings", "Navy", "#08263e"],
         ["Accent line / highlights", "Red", "#ec474e"],
         ["Subheadings / links", "Blue", "#518dca"],
         ["Alternating row background", "Light gray", "#f1f2f2"]],
        widths=[160, 80, 80])

    # 10. Security
    h1("10. Security Architecture")
    body("Authentication: JWT (HS256) with 24-hour expiry. Passwords hashed with bcrypt (passlib). Role-based access control (RBAC) enforced at each endpoint. CORS configurable via CORS_ORIGINS env var. File uploads validated by content type and size (max 10MB). Settlement proof paths use UUID segments to prevent enumeration.")
    sp()
    tbl(["Security Control", "Implementation"],
        [["Authentication", "JWT HS256, 24h expiry, stored in localStorage"],
         ["Password Storage", "bcrypt via passlib 1.7.4 / bcrypt 4.1.3"],
         ["Authorization", "Role-based (admin, trader, treasury) checked per endpoint"],
         ["CORS", "Configurable via CORS_ORIGINS environment variable"],
         ["File Upload", "Content-type whitelist, 10MB size limit, UUID path segments"],
         ["API Transport", "HTTPS via Kubernetes Ingress TLS termination"],
         ["Token Injection", "Axios interceptor auto-attaches Bearer token to all requests"]],
        widths=[100, 365])

    # 11. Business Rules
    elems.append(PageBreak())
    h1("11. Business Rules & Logic")
    for rule_name, rules in BUSINESS_RULES:
        h2(rule_name)
        for rule in rules:
            body(f"  {rule}")
        sp()


def tdd_docx_sections(doc):
    def h1(t): _docx_heading(doc, t, 1)
    def h2(t): _docx_heading(doc, t, 2)
    def h3(t): _docx_heading(doc, t, 3)
    def body(t): doc.add_paragraph(t)
    def tbl(headers, rows): _docx_table(doc, headers, rows)

    h1("1. System Overview")
    body("The FX Trading Tracker is a full-stack web application for managing foreign exchange deal tickets. It supports a three-role workflow: Traders create deal tickets, Treasury processes them (confirm/return), and Admins manage users, reference data, and audit trails. The platform is designed for on-premise deployment with switchable storage and database backends.")

    h1("2. System Architecture")
    h2("2.1 High-Level Architecture")
    body("The application follows a client-server architecture with a React SPA frontend communicating with a FastAPI REST backend via JSON over HTTPS.")
    tbl(["Layer", "Technology", "Version", "Description"],
        [["Frontend", "React SPA", "19.0.0", "Single-page app with lazy loading"],
         ["API Server", "FastAPI", "0.110.1", "Async REST API with Pydantic validation"],
         ["ASGI Server", "Uvicorn", "0.25.0", "Production ASGI server"],
         ["Database (Dev)", "MongoDB", "7.0.31", "Document database via motor async driver"],
         ["Database (Prod)", "Couchbase Enterprise", "SDK 4.6.0", "Distributed NoSQL with scopes/collections"],
         ["Storage (Dev)", "Emergent Object Storage", "API v1", "Cloud-based file storage"],
         ["Storage (Prod)", "S3-Compatible", "boto3 1.42.58", "On-premise object storage (Huawei OBS)"]])

    h2("2.2 Runtime Environment")
    tbl(["Component", "Version"], [[r[0], r[1]] for r in RUNTIME])

    h1("3. Backend Technology Stack")
    tbl(["Package", "Version", "Purpose"], [[p[0], p[1], p[2]] for p in TECH_STACK_BACKEND])

    h1("4. Frontend Technology Stack")
    h2("4.1 Core Dependencies")
    tbl(["Package", "Version", "Purpose"], [[p[0], p[1], p[2]] for p in TECH_STACK_FRONTEND])

    doc.add_page_break()
    h2("4.2 Shadcn/UI (Radix Primitives)")
    body("The UI component library is built on Radix UI primitives with Tailwind CSS styling.")
    tbl(["Package", "Version"], [[p[0], p[1]] for p in RADIX_COMPONENTS])

    doc.add_page_break()
    h1("5. Database Design")
    h2("5.1 Switchable Backend")
    body("The database layer is abstracted behind a factory pattern (services/database.py). The DB_TYPE environment variable controls which backend is active.")

    h2("5.2 Couchbase Scope/Collection Mapping")
    tbl(["Scope", "Collection", "MongoDB Equivalent", "Description"],
        [[s[0], s[1], s[2], s[3]] for s in SCOPE_MAP])

    h2("5.3 Data Models")
    for model_name, fields in DATA_MODELS:
        h3(f"Collection: {model_name}")
        tbl(["Field", "Type", "Description"], [[f[0], f[1], f[2]] for f in fields])

    doc.add_page_break()
    h1("6. Storage Abstraction Layer")
    tbl(["Backend", "Class", "Protocol", "Use Case"],
        [["emergent", "EmergentStorage", "Emergent REST API", "Cloud dev"],
         ["s3", "S3Storage", "S3 via boto3 (s3v4, path-style)", "On-prem (Huawei OBS, MinIO)"]])

    h1("7. Environment Variables")
    tbl(["Variable", "Purpose", "Example"], [[e[0], e[1], e[2]] for e in ENV_VARS])

    doc.add_page_break()
    h1("8. API Endpoint Reference")
    body("All endpoints prefixed with /api. Auth via Bearer JWT (24h expiry).")
    tbl(["Method", "Endpoint", "Access", "Description"],
        [[e[0], e[1], e[2], e[3]] for e in API_ENDPOINTS])

    doc.add_page_break()
    h1("9. Reports System")
    body("Seven FX trading reports, each supporting JSON (table preview), CSV, and PDF output formats.")
    tbl(["Report", "Description", "Filters", "Access"],
        [[r[0], r[1], r[2], r[3]] for r in REPORTS])

    h2("9.1 PDF Branding")
    tbl(["Element", "Color", "Hex"],
        [["Header/headings", "Navy", "#08263e"], ["Accent", "Red", "#ec474e"],
         ["Subheadings", "Blue", "#518dca"], ["Alt rows", "Light gray", "#f1f2f2"]])

    h1("10. Security Architecture")
    tbl(["Control", "Implementation"],
        [["Authentication", "JWT HS256, 24h expiry, localStorage"],
         ["Password Storage", "bcrypt via passlib 1.7.4 / bcrypt 4.1.3"],
         ["Authorization", "Role-based (admin, trader, treasury)"],
         ["CORS", "Configurable via CORS_ORIGINS env var"],
         ["File Upload", "Content-type whitelist, 10MB max, UUID paths"],
         ["Transport", "HTTPS via K8s Ingress TLS"],
         ["Token Injection", "Axios interceptor auto-attaches Bearer"]])

    doc.add_page_break()
    h1("11. Business Rules & Logic")
    for rule_name, rules in BUSINESS_RULES:
        h2(rule_name)
        for rule in rules:
            doc.add_paragraph(f"  {rule}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DOCUMENT 2: Deployment Guide                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def deploy_pdf_sections(elems, ss):
    def h1(t): elems.append(Paragraph(t, ss["H1"]))
    def h2(t): elems.append(Paragraph(t, ss["H2"]))
    def body(t): elems.append(Paragraph(t, ss["Body"]))
    def sp(n=6): elems.append(Spacer(1, n))
    def tbl(headers, rows, widths=None):
        data = [headers] + rows
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(_tbl_style())
        elems.append(t)
        sp()

    h1("1. Prerequisites")
    body("Before deploying, ensure the following are available in the target environment:")
    sp()
    tbl(["Requirement", "Version", "Notes"],
        [["Python", "3.11.15", "Runtime for FastAPI backend"],
         ["Node.js", "20.20.2", "For building React frontend"],
         ["MongoDB", "7.0.31", "Default database (or Couchbase Enterprise)"],
         ["Couchbase Enterprise", "7.0+", "On-premise database (optional, SDK 4.6.0)"],
         ["S3-Compatible Storage", "Any", "Huawei OBS, MinIO, or AWS S3 for file storage"],
         ["Supervisor", "Any", "Process manager for frontend and backend services"],
         ["HTTPS Certificate", "TLS 1.2+", "For production HTTPS termination"]],
        widths=[100, 60, 305])

    h1("2. Environment Configuration")
    h2("2.1 Backend (.env)")
    body("Create /app/backend/.env with the following variables. All values are required unless marked optional.")
    sp()
    tbl(["Variable", "Required", "Description"],
        [["MONGO_URL", "If DB_TYPE=mongodb", "MongoDB connection string"],
         ["DB_NAME", "If DB_TYPE=mongodb", "MongoDB database name"],
         ["DB_TYPE", "Yes", "mongodb or couchbase"],
         ["CB_CONNECTION_STRING", "If DB_TYPE=couchbase", "Couchbase cluster connection string"],
         ["CB_USERNAME", "If DB_TYPE=couchbase", "Couchbase username"],
         ["CB_PASSWORD", "If DB_TYPE=couchbase", "Couchbase password"],
         ["CB_BUCKET_NAME", "If DB_TYPE=couchbase", "Couchbase bucket name"],
         ["JWT_SECRET", "Yes", "Random secret for JWT signing (min 32 chars)"],
         ["STORAGE_TYPE", "Yes", "emergent or s3"],
         ["S3_ENDPOINT_URL", "If STORAGE_TYPE=s3", "S3-compatible endpoint"],
         ["S3_ACCESS_KEY_ID", "If STORAGE_TYPE=s3", "S3 access key"],
         ["S3_SECRET_ACCESS_KEY", "If STORAGE_TYPE=s3", "S3 secret key"],
         ["S3_BUCKET_NAME", "If STORAGE_TYPE=s3", "S3 bucket name"],
         ["S3_REGION", "If STORAGE_TYPE=s3", "S3 region"]],
        widths=[110, 85, 270])

    h2("2.2 Frontend (.env)")
    body("Set REACT_APP_BACKEND_URL to the production base URL (e.g., https://fx.company.com).")
    sp()

    h1("3. Switching Database Backend")
    h2("3.1 MongoDB (Default)")
    body("Set DB_TYPE=mongodb in backend/.env. Ensure MONGO_URL and DB_NAME are configured. The application auto-seeds default users and reference data on first startup.")
    sp()
    h2("3.2 Couchbase Enterprise")
    body("Set DB_TYPE=couchbase. Configure CB_CONNECTION_STRING, CB_USERNAME, CB_PASSWORD, and CB_BUCKET_NAME. On first startup, the application automatically: (1) Creates 4 scopes (identity, trading, reference, audit), (2) Creates 10 collections, (3) Creates primary and secondary indexes, (4) Seeds default users and reference data. Ensure the Couchbase user has Data Reader/Writer and Query/Index permissions on the bucket.")
    sp()

    h1("4. Switching Storage Backend")
    h2("4.1 S3-Compatible (Huawei OBS / MinIO)")
    body("Set STORAGE_TYPE=s3 and configure S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME, S3_REGION. The bucket must exist before starting the application. The S3 client uses s3v4 signature and path-style addressing for maximum compatibility.")
    sp()

    h1("5. Default User Accounts")
    body("The following accounts are auto-created on first startup if no users of that role exist:")
    sp()
    tbl(["Role", "Email", "Password"],
        [["Admin", "admin@fxtracker.com", "Admin@123"],
         ["Trader", "trader@fxtracker.com", "Trader@123"],
         ["Treasury", "treasury@fxtracker.com", "Treasury@123"],
         ["System Admin", "sysadmin@fxtracker.com", "SysAdmin@123"]],
        widths=[80, 160, 100])

    h1("6. Network Requirements")
    tbl(["Port", "Service", "Direction"],
        [["3000", "Frontend (React)", "Inbound (via reverse proxy)"],
         ["8001", "Backend (FastAPI)", "Inbound (via /api prefix routing)"],
         ["27017", "MongoDB", "Backend to DB (if MongoDB)"],
         ["11207", "Couchbase KV (TLS)", "Backend to DB (if Couchbase)"],
         ["18091", "Couchbase Mgmt (TLS)", "Backend to DB (if Couchbase)"],
         ["18093", "Couchbase Query (TLS)", "Backend to DB (if Couchbase)"],
         ["9000", "S3/MinIO", "Backend to Storage (if S3)"]],
        widths=[50, 140, 275])


def deploy_docx_sections(doc):
    def h1(t): _docx_heading(doc, t, 1)
    def h2(t): _docx_heading(doc, t, 2)
    def body(t): doc.add_paragraph(t)
    def tbl(h, r): _docx_table(doc, h, r)

    h1("1. Prerequisites")
    tbl(["Requirement", "Version", "Notes"],
        [["Python", "3.11.15", "FastAPI backend"],
         ["Node.js", "20.20.2", "React frontend build"],
         ["MongoDB", "7.0.31", "Default DB (or Couchbase)"],
         ["Couchbase Enterprise", "7.0+", "On-prem DB (optional)"],
         ["S3-Compatible Storage", "Any", "Huawei OBS, MinIO, or AWS S3"]])

    h1("2. Environment Configuration")
    h2("2.1 Backend (.env)")
    tbl(["Variable", "Required", "Description"],
        [["MONGO_URL", "If mongodb", "MongoDB connection string"],
         ["DB_NAME", "If mongodb", "MongoDB database name"],
         ["DB_TYPE", "Yes", "mongodb or couchbase"],
         ["CB_CONNECTION_STRING", "If couchbase", "Couchbase cluster"],
         ["CB_USERNAME", "If couchbase", "Couchbase user"],
         ["CB_PASSWORD", "If couchbase", "Couchbase password"],
         ["CB_BUCKET_NAME", "If couchbase", "Couchbase bucket"],
         ["JWT_SECRET", "Yes", "JWT signing key"],
         ["STORAGE_TYPE", "Yes", "emergent or s3"],
         ["S3_ENDPOINT_URL", "If s3", "S3 endpoint"],
         ["S3_ACCESS_KEY_ID", "If s3", "S3 access key"],
         ["S3_SECRET_ACCESS_KEY", "If s3", "S3 secret key"],
         ["S3_BUCKET_NAME", "If s3", "S3 bucket"],
         ["S3_REGION", "If s3", "S3 region"]])

    h1("3. Switching Database Backend")
    h2("3.1 MongoDB")
    body("Set DB_TYPE=mongodb. Auto-seeds on first startup.")
    h2("3.2 Couchbase Enterprise")
    body("Set DB_TYPE=couchbase. Auto-creates scopes, collections, indexes, and seeds data on first startup. Couchbase user needs Data Reader/Writer and Query/Index permissions.")

    h1("4. Switching Storage Backend")
    body("Set STORAGE_TYPE=s3 and configure S3_* variables. Uses s3v4 signature, path-style addressing. Bucket must exist.")

    h1("5. Default Accounts")
    tbl(["Role", "Email", "Password"],
        [["Admin", "admin@fxtracker.com", "Admin@123"],
         ["Trader", "trader@fxtracker.com", "Trader@123"],
         ["Treasury", "treasury@fxtracker.com", "Treasury@123"],
         ["System Admin", "sysadmin@fxtracker.com", "SysAdmin@123"]])

    h1("6. Network Requirements")
    tbl(["Port", "Service", "Direction"],
        [["3000", "Frontend", "Inbound"], ["8001", "Backend API", "Inbound"],
         ["27017", "MongoDB", "Backend->DB"], ["11207/18091/18093", "Couchbase (TLS)", "Backend->DB"],
         ["9000", "S3/MinIO", "Backend->Storage"]])


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN                                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    print("Generating Technical Design Document...")
    build_pdf("FX_Trading_Tracker_Technical_Design.pdf",
              "Technical Design Document",
              "FX Trading Tracker Platform  |  Architecture, APIs, Data Models & Technology Stack",
              tdd_pdf_sections)
    build_docx("FX_Trading_Tracker_Technical_Design.docx",
               "Technical Design Document",
               "FX Trading Tracker Platform  |  Architecture, APIs, Data Models & Technology Stack",
               tdd_docx_sections)

    print("Generating Deployment Guide...")
    build_pdf("FX_Trading_Tracker_Deployment_Guide.pdf",
              "Deployment & Configuration Guide",
              "FX Trading Tracker Platform  |  On-Premise Setup, Environment Variables & Network Requirements",
              deploy_pdf_sections)
    build_docx("FX_Trading_Tracker_Deployment_Guide.docx",
               "Deployment & Configuration Guide",
               "FX Trading Tracker Platform  |  On-Premise Setup, Environment Variables & Network Requirements",
               deploy_docx_sections)

    print(f"\nAll documents generated in {OUT_DIR}/")
