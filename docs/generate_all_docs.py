"""
Generate BRD, SRS, and User Manual for FX Trading Tracker.
Outputs PDF + DOCX for each document with embedded screenshots and branding.
"""
import os, io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

C_NAVY = colors.HexColor("#08263e")
C_RED = colors.HexColor("#ec474e")
C_BLUE = colors.HexColor("#518dca")
C_GRAY = colors.HexColor("#f1f2f2")
NAVY_RGB = RGBColor(0x08, 0x26, 0x3e)
RED_RGB = RGBColor(0xec, 0x47, 0x4e)
BLUE_RGB = RGBColor(0x51, 0x8d, 0xca)

OUT = "/app/docs"
IMG = "/app/docs/screenshots"
GEN = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
VER = "2.0"
PDF_IMG_W = 170 * mm
DOCX_IMG_W = Inches(6.0)

def _ip(name):
    return os.path.join(IMG, name)

def _ie(name):
    return os.path.isfile(_ip(name))


# ══════════════════════════════════════════════════════════════════════════════
# PDF UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def _ss():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("DocTitle", parent=ss["Title"], fontSize=26, textColor=C_NAVY, spaceAfter=6, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("DocSub", parent=ss["Normal"], fontSize=12, textColor=C_BLUE, spaceAfter=20))
    ss.add(ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, textColor=C_NAVY, spaceBefore=20, spaceAfter=8, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, textColor=C_NAVY, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("H3", parent=ss["Heading3"], fontSize=10, textColor=C_BLUE, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("Body", parent=ss["Normal"], fontSize=9, leading=13, alignment=TA_JUSTIFY))
    ss.add(ParagraphStyle("BodySm", parent=ss["Normal"], fontSize=8, leading=11))
    ss.add(ParagraphStyle("Caption", parent=ss["Normal"], fontSize=7.5, leading=10, textColor=C_BLUE, alignment=TA_CENTER, spaceAfter=10, fontName="Helvetica-Oblique"))
    ss.add(ParagraphStyle("Note", parent=ss["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#555"), leftIndent=12, fontName="Helvetica-Oblique"))
    ss.add(ParagraphStyle("CodeBlk", parent=ss["Normal"], fontSize=7.5, leading=10, fontName="Courier", backColor=C_GRAY, leftIndent=10, rightIndent=10, spaceBefore=4, spaceAfter=4))
    ss.add(ParagraphStyle("CellTxt", parent=ss["Normal"], fontSize=7, leading=9))
    ss.add(ParagraphStyle("BulletPt", parent=ss["Normal"], fontSize=9, leading=13, leftIndent=18, bulletIndent=6))
    return ss

def _ts():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])

def _ph(canvas, doc, title):
    canvas.saveState()
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, doc.pagesize[1]-10*mm, doc.pagesize[0], 10*mm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(12*mm, doc.pagesize[1]-7*mm, f"FX Trading Tracker  |  {title}")
    canvas.setFont("Helvetica", 6)
    canvas.drawRightString(doc.pagesize[0]-12*mm, doc.pagesize[1]-7*mm, f"v{VER}  |  {GEN}")
    canvas.setStrokeColor(C_RED); canvas.setLineWidth(1.2)
    canvas.line(0, doc.pagesize[1]-10*mm, doc.pagesize[0], doc.pagesize[1]-10*mm)
    canvas.setFillColor(C_NAVY); canvas.setFont("Helvetica", 6)
    canvas.drawRightString(doc.pagesize[0]-12*mm, 7*mm, f"Page {doc.page}")
    canvas.restoreState()

def _pi(elems, fn, cap, s):
    if _ie(fn):
        fp = _ip(fn)
        ir = ImageReader(fp); iw, ih = ir.getSize()
        dw = min(PDF_IMG_W, iw); dh = dw * (ih / iw)
        im = Image(fp, width=dw, height=dh); im.hAlign = 'CENTER'
        elems.append(Spacer(1, 6)); elems.append(im)
        if cap: elems.append(Paragraph(cap, s["Caption"]))
        else: elems.append(Spacer(1, 6))

def _build_pdf(path, title, content_fn):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16*mm, bottomMargin=14*mm, leftMargin=14*mm, rightMargin=14*mm)
    s = _ss(); e = []
    content_fn(e, s)
    header = lambda c, d: _ph(c, d, title)
    doc.build(e, onFirstPage=header, onLaterPages=header)
    buf.seek(0)
    with open(path, "wb") as f: f.write(buf.read())
    print(f"  PDF: {path}")


# ══════════════════════════════════════════════════════════════════════════════
# DOCX UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def _dh(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs: r.font.color.rgb = NAVY_RGB
    return h

def _dt(doc, headers, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs: r.font.size = Pt(8); r.font.bold = True; r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)
        sh = c._element.get_or_add_tcPr()
        sh.append(sh.makeelement(qn("w:shd"), {qn("w:val"):"clear", qn("w:color"):"auto", qn("w:fill"):"08263e"}))
    for ri, row in enumerate(rows):
        for ci, v in enumerate(row):
            c = t.rows[ri+1].cells[ci]; c.text = str(v)
            for p in c.paragraphs:
                for r in p.runs: r.font.size = Pt(7.5)
            if ri % 2 == 1:
                sh = c._element.get_or_add_tcPr()
                sh.append(sh.makeelement(qn("w:shd"), {qn("w:val"):"clear", qn("w:color"):"auto", qn("w:fill"):"f1f2f2"}))

def _di(doc, fn, cap=None):
    if _ie(fn):
        doc.add_picture(_ip(fn), width=DOCX_IMG_W)
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if cap:
            c = doc.add_paragraph(cap); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in c.runs: r.font.size = Pt(8); r.font.color.rgb = BLUE_RGB; r.font.italic = True

def _dn(doc, text):
    p = doc.add_paragraph(); r = p.add_run(text); r.font.size = Pt(8); r.font.italic = True; r.font.color.rgb = RGBColor(0x55,0x55,0x55)

def _build_docx(path, title, content_fn):
    doc = Document()
    for sec in doc.sections: sec.top_margin = Cm(2); sec.bottom_margin = Cm(1.5); sec.left_margin = Cm(2); sec.right_margin = Cm(2)
    content_fn(doc)
    doc.save(path)
    print(f"  DOCX: {path}")

def _title_page_pdf(e, s, title, subtitle):
    e.append(Spacer(1, 60))
    e.append(Paragraph(title, s["DocTitle"]))
    e.append(Paragraph(subtitle, s["DocSub"]))
    e.append(Spacer(1, 10))
    e.append(Paragraph(f"Generated: {GEN}", s["BodySm"]))
    e.append(Paragraph("Classification: CONFIDENTIAL", s["BodySm"]))
    e.append(PageBreak())

def _title_page_docx(doc, title, subtitle):
    t = doc.add_heading(title, 0)
    for r in t.runs: r.font.color.rgb = NAVY_RGB
    sub = doc.add_paragraph(subtitle)
    for r in sub.runs: r.font.color.rgb = BLUE_RGB; r.font.size = Pt(11)
    m = doc.add_paragraph(f"Generated: {GEN}\nClassification: CONFIDENTIAL")
    for r in m.runs: r.font.size = Pt(8)
    doc.add_page_break()


# ══════════════════════════════════════════════════════════════════════════════
# 1. BRD CONTENT
# ══════════════════════════════════════════════════════════════════════════════
def brd_pdf_content(e, s):
    h1=lambda t: e.append(Paragraph(t, s["H1"]))
    h2=lambda t: e.append(Paragraph(t, s["H2"]))
    b=lambda t: e.append(Paragraph(t, s["Body"]))
    sp=lambda n=6: e.append(Spacer(1, n))
    note=lambda t: e.append(Paragraph(t, s["Note"]))
    bul=lambda t: e.append(Paragraph(t, s["BulletPt"], bulletText="\u2022"))
    img=lambda fn,cap=None: _pi(e, fn, cap, s)
    def tbl(hd, rows, w=None):
        t = Table([hd]+rows, colWidths=w, repeatRows=1); t.setStyle(_ts()); e.append(t); sp()

    _title_page_pdf(e, s, "Business Requirements Document", f"FX Trading Tracker Platform  |  Version {VER}")

    # TOC
    h1("Table of Contents")
    for t in ["1. Executive Summary","2. Business Objectives","3. Stakeholders","4. Scope","5. Business Requirements",
              "6. Workflow & Process Flows","7. Data Requirements","8. Non-Functional Requirements",
              "9. Assumptions & Constraints","10. Acceptance Criteria","11. Glossary"]:
        b(f"    {t}")
    e.append(PageBreak())

    # 1
    h1("1. Executive Summary")
    b("The FX Trading Tracker is a web-based platform designed to streamline the management of foreign exchange deal tickets within a multi-role operational environment. The system replaces manual spreadsheet-based tracking with a structured, auditable workflow that connects traders, treasury processors, and administrators.")
    sp()
    b("The platform supports the complete deal lifecycle from ticket creation through treasury confirmation, with built-in settlement proof management, comprehensive reporting, and full audit trail capabilities. It is designed for on-premise deployment with switchable database (MongoDB/Couchbase Enterprise) and storage (Emergent/S3-compatible/Huawei OBS) backends.")
    img("02_dashboard.png", "Figure 1.1 - FX Trading Tracker Dashboard")
    e.append(PageBreak())

    # 2
    h1("2. Business Objectives")
    bul("<b>Operational Efficiency</b> - Replace manual spreadsheet tracking with a structured deal ticket workflow reducing processing time by 60%.")
    bul("<b>Compliance & Auditability</b> - Provide a full audit trail of every action, settlement proof management, and role-based access controls.")
    bul("<b>Accuracy</b> - Eliminate data entry errors through structured forms, validation rules, and automated calculations.")
    bul("<b>Visibility</b> - Real-time dashboards, 8 report types, and CSV/PDF exports give management instant insight into trading operations.")
    bul("<b>Scalability</b> - Switchable database and storage backends enable on-premise deployment at enterprise scale.")
    bul("<b>Crypto Support</b> - Native crypto wallet addressing with blockchain network selection (SOLANA, ETHEREUM, TRON).")
    e.append(PageBreak())

    # 3
    h1("3. Stakeholders")
    tbl(["Stakeholder", "Role", "Interest"],
        [["FX Traders", "Primary user", "Create deal tickets, manage client proofs, track deal status"],
         ["Treasury Team", "Processor", "Review, confirm/return deals, upload processor proofs"],
         ["Operations Admin", "Administrator", "Manage users, reference data, reports, audit trail"],
         ["System Admin", "IT/DevOps", "Database management, system exports, controlled reset"],
         ["Management", "Consumer", "Reports, dashboards, volume analysis"],
         ["Compliance/Audit", "Auditor", "Audit trail, transaction history, settlement proof review"]],
        w=[90, 70, 305])
    e.append(PageBreak())

    # 4
    h1("4. Scope")
    h2("4.1 In-Scope")
    for item in ["Multi-role authentication (Trader, Treasury, Admin, System Admin)",
                 "Deal ticket creation with Buy/Sell transaction types",
                 "6 transfer types: FX Crypto, FX Local, FX Bank Deal, FX-Intercompany, FX - Corporate Settlement, PDAX Withdrawal",
                 "Counterparty management for PJL Group entities",
                 "Bank and crypto account management with CSV/Excel bulk import (including legacy fld_* format)",
                 "Settlement proof upload/management (client and processor)",
                 "Treasury confirmation workflow with return/resubmit cycle",
                 "8 report types with CSV/PDF export, admin-configurable permissions",
                 "Full audit trail with action-level logging",
                 "FX Client and bank account reference data management",
                 "System administration (DB stats, exports, controlled reset)",
                 "On-premise deployment readiness (switchable MongoDB/Couchbase, Emergent/S3 storage)"]:
        bul(item)
    sp()
    h2("4.2 Out-of-Scope (Future)")
    for item in ["Email/SMS notifications","Scheduled report delivery","Approval workflow for TMS","Real-time price feeds","Mobile native app"]:
        bul(item)
    e.append(PageBreak())

    # 5
    h1("5. Business Requirements")
    h2("BR-001: Deal Ticket Management")
    b("The system shall enable authorized traders to create, view, and manage FX deal tickets with structured fields including client name, transaction type (Buy/Sell), transfer type, currency pair, amounts, rates, and bank/crypto account details.")
    img("04_new_deal.png", "Figure 5.1 - New Deal Ticket Form")
    sp()
    h2("BR-002: Treasury Processing Workflow")
    b("Treasury processors shall be able to review pending deals, upload settlement proofs, and confirm or return deals with mandatory remarks. At least one settlement proof must exist before confirmation is allowed.")
    img("06_treasury_queue.png", "Figure 5.2 - Treasury Deal Queue")
    sp()
    h2("BR-003: Settlement Proof Management")
    b("Both traders (client proofs) and treasury (processor proofs) shall be able to upload, view, and delete settlement proof documents (images, PDFs) associated with deals.")
    sp()
    h2("BR-004: Reference Data Management")
    b("Administrators shall manage FX clients, banks, bank accounts, counterparties, currencies, transaction types, and transfer types. Bulk import from CSV/Excel shall be supported for FX clients and bank accounts.")
    img("07_reference_data.png", "Figure 5.3 - Reference Data Management (FX Client tab)")
    sp()
    h2("BR-005: Reporting & Analytics")
    b("The system shall provide 8 pre-built reports (Deal Blotter, Settlement, Open Positions, Audit Trail, User Activity, Volume Summary, Client Activity, TMS/SAP) with server-side pagination, filterable date ranges, and CSV/PDF export capabilities.")
    img("11_reports.png", "Figure 5.4 - Reports Page")
    sp()
    h2("BR-006: Audit Trail")
    b("Every significant action (deal creation, status change, proof upload/deletion, user management, reference data changes) shall be logged with timestamp, user, action type, and details.")
    sp()
    h2("BR-007: Multi-Bank Account Import")
    b("The system shall support bulk import of bank accounts from CSV/Excel files in both simple (account_number, account_name) and legacy (fld_AccountNo, fld_BranchAddress, fld_BankCode) formats, with automatic bank matching/creation and persistence of extended fields (currency_code, account_type, bank_address).")
    e.append(PageBreak())

    # 6
    h1("6. Workflow & Process Flows")
    h2("6.1 Deal Lifecycle Workflow")
    b("The deal follows a defined state machine:")
    sp()
    b("<b>Created</b> → <b>Pending</b> → <b>Confirmed</b> (by Treasury)")
    b("<b>Created</b> → <b>Pending</b> → <b>Returned</b> (by Treasury) → <b>Edited/Resubmitted</b> → <b>Pending</b>")
    b("<b>Created</b> → <b>Pending</b> → <b>Cancelled</b> (by Trader)")
    sp()
    tbl(["State", "Triggered By", "Next States", "Actions Available"],
        [["Pending", "Trader creates deal", "Confirmed, Returned, Cancelled", "Treasury: Review, Confirm, Return; Trader: Cancel"],
         ["Confirmed", "Treasury confirms", "Terminal", "View only, audit logged"],
         ["Returned", "Treasury returns", "Pending (via resubmit)", "Trader: Edit, Resubmit"],
         ["Cancelled", "Trader cancels", "Terminal", "View only, audit logged"]],
        w=[65, 100, 100, 200])
    sp()
    h2("6.2 Settlement Proof Workflow")
    b("1. Trader creates deal (optionally attaches client proofs).")
    b("2. Deal enters pending queue for Treasury.")
    b("3. Treasury reviews deal, uploads processor proofs.")
    b("4. Treasury confirms deal (requires >= 1 total proof) or returns with remarks.")
    b("5. If returned, Trader edits and resubmits.")
    sp()
    h2("6.3 FX-Intercompany Dual-Line Workflow")
    b("FX-Intercompany deals generate two settlement lines: .1 (Sell side) and .2 (Buy side), each with their own counterparty ours accounts. Both lines appear in Settlement and TMS reports.")
    e.append(PageBreak())

    # 7
    h1("7. Data Requirements")
    tbl(["Entity", "Key Fields", "Source"],
        [["Deal Ticket", "Reference, Client, Type, Transfer Type, Currency Pair, Amount, Rate, Dates, Bank/Crypto Accounts, Network", "Trader input"],
         ["FX Client", "Name, Code, Type (Customer/Vendor)", "Admin input or CSV import"],
         ["Bank", "Name, Code, SWIFT Code", "Admin input or auto-created from import"],
         ["Bank Account", "Account Number, Name, Currency Code, Type, Bank Address, Contact", "Admin input or CSV/Excel import"],
         ["Counterparty", "Name, Code (CLSC, PJ, Verite, etc.)", "Admin input"],
         ["Currency", "Code, Name, Symbol, Type (fiat/stablecoin/crypto)", "Seeded, admin-editable"],
         ["Settlement Proof", "File URL, Type (client/processor), Upload Timestamp", "Trader/Treasury upload"],
         ["Audit Log", "Action, Entity, User, Timestamp, Details", "System-generated"]],
        w=[70, 250, 145])
    e.append(PageBreak())

    # 8
    h1("8. Non-Functional Requirements")
    tbl(["Category", "Requirement"],
        [["Performance", "Dashboard loads in < 2 seconds. Report pagination supports 10,000+ records."],
         ["Security", "Role-based access control. JWT authentication. Password hashing (bcrypt). Audit logging."],
         ["Availability", "On-premise deployment with hot-reload development. Supervisor-managed processes."],
         ["Scalability", "Switchable MongoDB/Couchbase database backends. Switchable Emergent/S3 storage."],
         ["Maintainability", "Modular architecture with database abstraction layer and storage abstraction."],
         ["Data Integrity", "Foreign key relationships via application logic. Duplicate detection on imports."],
         ["Browser Support", "Modern browsers (Chrome, Firefox, Safari, Edge). Responsive design."]],
        w=[80, 385])
    e.append(PageBreak())

    # 9
    h1("9. Assumptions & Constraints")
    h2("Assumptions")
    bul("Users have modern web browsers with JavaScript enabled.")
    bul("Network connectivity between browser and application server is reliable.")
    bul("On-premise deployment will provide necessary infrastructure (servers, database, storage).")
    bul("Bank account data in legacy format follows the fld_* column naming convention.")
    sp()
    h2("Constraints")
    bul("The system does not provide real-time FX rate feeds — rates are manually entered per deal.")
    bul("Settlement proofs are limited to images (JPEG, PNG, WebP, GIF) and PDFs, max 10MB per file.")
    bul("The approval workflow for TMS Approver field is not yet implemented.")
    bul("Email/SMS notifications are not currently available.")
    e.append(PageBreak())

    # 10
    h1("10. Acceptance Criteria")
    tbl(["ID", "Criteria", "Validation"],
        [["AC-01", "Trader can create a deal ticket with all required fields", "Deal appears in pending queue"],
         ["AC-02", "Treasury can confirm/return deals with mandatory remarks", "Status changes, audit logged"],
         ["AC-03", "Settlement proofs can be uploaded and viewed", "Files stored, displayed in deal detail"],
         ["AC-04", "Admin can import 1000+ bank accounts via CSV", "Accounts created, duplicates skipped"],
         ["AC-05", "Reports generate with correct data and export to CSV/PDF", "Data matches, files download"],
         ["AC-06", "Audit trail captures all significant actions", "Actions logged with correct metadata"],
         ["AC-07", "System admin can reset database retaining users/ref data", "Deals cleared, users retained"]],
        w=[35, 230, 200])
    e.append(PageBreak())

    # 11
    h1("11. Glossary")
    tbl(["Term", "Definition"],
        [["Deal Ticket", "An FX trade record with client, currency, amount, rate, and account details"],
         ["Settlement Proof", "Documentary evidence of fund transfer (image or PDF)"],
         ["Counterparty", "PJL Group entity (CLSC, PJ, Verite) used in FX Local/Intercompany deals"],
         ["Transfer Type", "Classification of the FX transaction (FX Crypto, FX Local, FX Bank Deal, etc.)"],
         ["TMS", "Treasury Management System — SAP-compatible export format"],
         ["FX-Intercompany", "Transfer between PJL Group entities generating dual settlement lines"],
         ["Crypto Network", "Blockchain network (SOLANA, ETHEREUM, TRON) for crypto transactions"]],
        w=[80, 385])


def brd_docx_content(doc):
    _title_page_docx(doc, "Business Requirements Document", f"FX Trading Tracker Platform  |  Version {VER}")

    _dh(doc, "1. Executive Summary")
    doc.add_paragraph("The FX Trading Tracker is a web-based platform designed to streamline the management of foreign exchange deal tickets within a multi-role operational environment. The system replaces manual spreadsheet-based tracking with a structured, auditable workflow that connects traders, treasury processors, and administrators.")
    doc.add_paragraph("The platform supports the complete deal lifecycle from ticket creation through treasury confirmation, with built-in settlement proof management, comprehensive reporting, and full audit trail capabilities. It is designed for on-premise deployment with switchable database (MongoDB/Couchbase Enterprise) and storage (Emergent/S3-compatible/Huawei OBS) backends.")
    _di(doc, "02_dashboard.png", "Figure 1.1 - FX Trading Tracker Dashboard")
    doc.add_page_break()

    _dh(doc, "2. Business Objectives")
    for obj in ["Operational Efficiency - Replace manual spreadsheet tracking with structured deal ticket workflow.",
                "Compliance & Auditability - Full audit trail, settlement proof management, role-based access.",
                "Accuracy - Structured forms, validation, automated calculations.",
                "Visibility - Dashboards, 8 report types, CSV/PDF exports.",
                "Scalability - Switchable database (MongoDB/Couchbase) and storage (Emergent/S3) backends.",
                "Crypto Support - Native crypto wallet with blockchain network selection (SOLANA/ETHEREUM/TRON)."]:
        doc.add_paragraph(obj, style='List Bullet')
    doc.add_page_break()

    _dh(doc, "3. Stakeholders")
    _dt(doc, ["Stakeholder", "Role", "Interest"],
        [["FX Traders", "Primary user", "Create deal tickets, manage client proofs, track deal status"],
         ["Treasury Team", "Processor", "Review, confirm/return deals, upload processor proofs"],
         ["Operations Admin", "Administrator", "Manage users, reference data, reports, audit trail"],
         ["System Admin", "IT/DevOps", "Database management, system exports, controlled reset"],
         ["Management", "Consumer", "Reports, dashboards, volume analysis"],
         ["Compliance/Audit", "Auditor", "Audit trail, transaction history, settlement proof review"]])
    doc.add_page_break()

    _dh(doc, "4. Scope")
    _dh(doc, "4.1 In-Scope", 2)
    for item in ["Multi-role authentication (Trader, Treasury, Admin, System Admin)",
                 "Deal ticket CRUD with Buy/Sell types and 6 transfer types",
                 "Counterparty management, bank/crypto account management with CSV/Excel bulk import",
                 "Settlement proof upload/management, treasury confirmation workflow",
                 "8 report types with CSV/PDF export, admin-configurable permissions",
                 "Full audit trail, system administration (DB stats/exports/reset)",
                 "On-premise deployment readiness (switchable MongoDB/Couchbase, Emergent/S3)"]:
        doc.add_paragraph(item, style='List Bullet')
    _dh(doc, "4.2 Out-of-Scope (Future)", 2)
    for item in ["Email/SMS notifications","Scheduled reports","Approval workflow","Real-time price feeds","Mobile native app"]:
        doc.add_paragraph(item, style='List Bullet')
    doc.add_page_break()

    _dh(doc, "5. Business Requirements")
    _dh(doc, "BR-001: Deal Ticket Management", 2)
    doc.add_paragraph("The system shall enable authorized traders to create, view, and manage FX deal tickets with structured fields.")
    _di(doc, "04_new_deal.png", "Figure 5.1 - New Deal Ticket Form")
    _dh(doc, "BR-002: Treasury Processing Workflow", 2)
    doc.add_paragraph("Treasury processors shall review pending deals, upload proofs, and confirm or return deals with mandatory remarks.")
    _di(doc, "06_treasury_queue.png", "Figure 5.2 - Treasury Deal Queue")
    _dh(doc, "BR-003: Reference Data Management", 2)
    _di(doc, "07_reference_data.png", "Figure 5.3 - Reference Data Management")
    _dh(doc, "BR-004: Reporting & Analytics", 2)
    _di(doc, "11_reports.png", "Figure 5.4 - Reports Page")
    _dh(doc, "BR-005: Multi-Bank Account Import", 2)
    doc.add_paragraph("Support CSV/Excel import in both simple and legacy fld_* formats with auto bank matching/creation.")
    doc.add_page_break()

    _dh(doc, "6. Workflow & Process Flows")
    _dh(doc, "6.1 Deal Lifecycle", 2)
    _dt(doc, ["State", "Triggered By", "Next States", "Actions"],
        [["Pending", "Trader creates deal", "Confirmed, Returned, Cancelled", "Treasury: Review/Confirm/Return; Trader: Cancel"],
         ["Confirmed", "Treasury confirms", "Terminal", "View only"],
         ["Returned", "Treasury returns", "Pending (resubmit)", "Trader: Edit, Resubmit"],
         ["Cancelled", "Trader cancels", "Terminal", "View only"]])
    doc.add_page_break()

    _dh(doc, "7. Data Requirements")
    _dt(doc, ["Entity", "Key Fields", "Source"],
        [["Deal Ticket", "Reference, Client, Type, Pair, Amount, Rate, Accounts, Network", "Trader"],
         ["FX Client", "Name, Code, Type", "Admin/CSV"],
         ["Bank Account", "Number, Name, Currency, Type, Address", "Admin/CSV"],
         ["Counterparty", "Name, Code", "Admin"],
         ["Settlement Proof", "File URL, Type, Timestamp", "Upload"],
         ["Audit Log", "Action, Entity, User, Timestamp, Details", "System"]])
    doc.add_page_break()

    _dh(doc, "8. Non-Functional Requirements")
    _dt(doc, ["Category", "Requirement"],
        [["Performance", "Dashboard < 2s. Pagination supports 10,000+ records."],
         ["Security", "RBAC, JWT, bcrypt, audit logging."],
         ["Scalability", "Switchable MongoDB/Couchbase and Emergent/S3."],
         ["Browser Support", "Chrome, Firefox, Safari, Edge. Responsive."]])
    doc.add_page_break()

    _dh(doc, "9. Assumptions & Constraints")
    for a in ["Users have modern browsers with JS enabled.","On-premise infra provided.","Legacy CSV uses fld_* columns."]:
        doc.add_paragraph(a, style='List Bullet')
    _dh(doc, "Constraints", 2)
    for c in ["No real-time FX rate feeds.","Proofs limited to images/PDF, 10MB max.","No approval workflow yet."]:
        doc.add_paragraph(c, style='List Bullet')

    _dh(doc, "10. Acceptance Criteria")
    _dt(doc, ["ID", "Criteria", "Validation"],
        [["AC-01", "Trader creates deal with all required fields", "Deal in pending queue"],
         ["AC-02", "Treasury confirms/returns with remarks", "Status changes, audit logged"],
         ["AC-03", "Admin imports 1000+ bank accounts via CSV", "Created, duplicates skipped"],
         ["AC-04", "Reports generate correctly with CSV/PDF export", "Data matches, files download"],
         ["AC-05", "Audit trail captures all actions", "Correct metadata logged"]])

    _dh(doc, "11. Glossary")
    _dt(doc, ["Term", "Definition"],
        [["Deal Ticket", "FX trade record with client, currency, amount, rate, accounts"],
         ["Settlement Proof", "Documentary evidence of fund transfer"],
         ["Counterparty", "PJL Group entity for FX Local/Intercompany deals"],
         ["TMS", "Treasury Management System (SAP-compatible export)"],
         ["Crypto Network", "Blockchain (SOLANA/ETHEREUM/TRON) for crypto transactions"]])


# ══════════════════════════════════════════════════════════════════════════════
# 2. SRS CONTENT
# ══════════════════════════════════════════════════════════════════════════════
def srs_pdf_content(e, s):
    h1=lambda t: e.append(Paragraph(t, s["H1"]))
    h2=lambda t: e.append(Paragraph(t, s["H2"]))
    h3=lambda t: e.append(Paragraph(t, s["H3"]))
    b=lambda t: e.append(Paragraph(t, s["Body"]))
    sp=lambda n=6: e.append(Spacer(1, n))
    note=lambda t: e.append(Paragraph(t, s["Note"]))
    bul=lambda t: e.append(Paragraph(t, s["BulletPt"], bulletText="\u2022"))
    code=lambda t: e.append(Paragraph(t, s["CodeBlk"]))
    img=lambda fn,cap=None: _pi(e, fn, cap, s)
    def tbl(hd, rows, w=None):
        t = Table([hd]+rows, colWidths=w, repeatRows=1); t.setStyle(_ts()); e.append(t); sp()

    _title_page_pdf(e, s, "Software Requirements Specification", f"FX Trading Tracker Platform  |  Version {VER}")

    # TOC
    h1("Table of Contents")
    for t in ["1. Introduction","2. System Architecture","3. Technology Stack","4. Functional Requirements",
              "5. API Specification","6. Data Models","7. Security Requirements",
              "8. User Interface Specifications","9. Deployment Architecture","10. Integration Points"]:
        b(f"    {t}")
    e.append(PageBreak())

    # 1
    h1("1. Introduction")
    h2("1.1 Purpose")
    b("This Software Requirements Specification defines the technical requirements for the FX Trading Tracker platform, a web-based application for managing foreign exchange deal tickets across trader, treasury, and administrative roles.")
    h2("1.2 Scope")
    b("The system consists of a React single-page application frontend, a FastAPI REST backend, MongoDB/Couchbase database, and Emergent/S3-compatible object storage. It supports the full deal lifecycle with settlement proof management, 8 report types, and comprehensive audit logging.")
    e.append(PageBreak())

    # 2
    h1("2. System Architecture")
    h2("2.1 Architecture Overview")
    b("The application follows a three-tier architecture:")
    bul("<b>Presentation Layer</b> — React 19 SPA with Shadcn/UI components, TailwindCSS, Axios HTTP client")
    bul("<b>Application Layer</b> — FastAPI REST API with Pydantic validation, JWT authentication, ReportLab PDF generation")
    bul("<b>Data Layer</b> — Switchable database (MongoDB via Motor / Couchbase Enterprise SDK) with abstraction layer; Switchable object storage (Emergent / S3-compatible via boto3)")
    sp()
    h2("2.2 Component Diagram")
    tbl(["Component", "Technology", "Responsibility"],
        [["Frontend SPA", "React 19, TailwindCSS, Shadcn/UI", "User interface, form validation, API calls"],
         ["API Server", "FastAPI, Uvicorn", "REST endpoints, business logic, JWT auth"],
         ["Database Abstraction", "database.py, db_mongo.py, db_couchbase.py", "Switchable DB backend with cursor wrappers"],
         ["Storage Abstraction", "storage.py", "Switchable file storage (Emergent/S3)"],
         ["Report Engine", "reports.py, ReportLab", "PDF/CSV generation with branded templates"],
         ["MongoDB", "Motor (async driver)", "Document storage, text indexes"],
         ["Couchbase", "SDK 4.6, N1QL", "Alternative enterprise DB with scopes/collections"]],
        w=[85, 140, 240])
    e.append(PageBreak())

    # 3
    h1("3. Technology Stack")
    h2("3.1 Backend")
    tbl(["Package", "Version", "Purpose"],
        [["FastAPI", "0.110.1", "REST API framework"],
         ["Uvicorn", "0.25.0", "ASGI server"],
         ["Pydantic", "2.12.5", "Data validation"],
         ["Motor", "3.7.1", "Async MongoDB driver"],
         ["Couchbase SDK", "4.6.0", "Couchbase Enterprise client"],
         ["boto3", "1.42.58", "S3-compatible storage"],
         ["ReportLab", "4.4.10", "PDF generation"],
         ["python-jose", "3.4.0", "JWT token handling"],
         ["bcrypt", "4.3.0", "Password hashing"],
         ["python-docx", "1.1.2", "DOCX generation"],
         ["openpyxl", "3.1.5", "Excel file parsing"]],
        w=[85, 60, 320])
    sp()
    h2("3.2 Frontend")
    tbl(["Package", "Version", "Purpose"],
        [["React", "19.0.0", "UI framework"],
         ["React Router", "7.5.1", "Client-side routing"],
         ["TailwindCSS", "3.4.17", "Utility-first CSS"],
         ["Shadcn/UI", "latest", "Component library (Radix-based)"],
         ["Axios", "1.8.4", "HTTP client"],
         ["Recharts", "2.15.3", "Charts and data visualization"],
         ["date-fns", "4.1.0", "Date formatting"],
         ["sonner", "2.0.3", "Toast notifications"]],
        w=[85, 60, 320])
    e.append(PageBreak())

    # 4
    h1("4. Functional Requirements")
    h2("FR-001: Authentication & Authorization")
    tbl(["ID", "Requirement"],
        [["FR-001.1", "System shall authenticate users via email/password with JWT tokens"],
         ["FR-001.2", "System shall enforce role-based access (Trader, Treasury, Admin, Sysadmin)"],
         ["FR-001.3", "JWT tokens shall expire after 24 hours"],
         ["FR-001.4", "Passwords shall be hashed with bcrypt"]],
        w=[60, 405])
    sp()
    h2("FR-002: Deal Management")
    tbl(["ID", "Requirement"],
        [["FR-002.1", "Traders shall create deal tickets with: client name, transaction type (Buy/Sell), transfer type, deal/value dates, currency, amount, rate, bank/crypto accounts"],
         ["FR-002.2", "System shall auto-generate sequential reference numbers (FX-YYYYMMDD-NNNN)"],
         ["FR-002.3", "Deals shall support 6 transfer types with conditional form logic"],
         ["FR-002.4", "Crypto accounts shall require network selection (SOLANA/ETHEREUM/TRON)"],
         ["FR-002.5", "FX-Intercompany deals shall have dual Ours sections (Selling + Buying)"],
         ["FR-002.6", "FX Bank Deal shall hide destination fields"],
         ["FR-002.7", "FX - Corporate Settlement shall behave identically to FX Local"]],
        w=[60, 405])
    sp()
    h2("FR-003: Treasury Processing")
    tbl(["ID", "Requirement"],
        [["FR-003.1", "Treasury shall view pending deals in a queue with customizable columns"],
         ["FR-003.2", "Treasury shall confirm or return deals with mandatory remarks"],
         ["FR-003.3", "Confirmation shall require >= 1 settlement proof (client or processor)"],
         ["FR-003.4", "Returned deals shall be editable and resubmittable by the original trader"]],
        w=[60, 405])
    sp()
    h2("FR-004: Settlement Proofs")
    tbl(["ID", "Requirement"],
        [["FR-004.1", "Traders upload client proofs (images/PDF, max 10MB)"],
         ["FR-004.2", "Treasury uploads processor proofs"],
         ["FR-004.3", "Client proofs not applicable for FX Bank Deal"],
         ["FR-004.4", "Proofs stored via storage abstraction (Emergent or S3)"]],
        w=[60, 405])
    sp()
    h2("FR-005: Reference Data")
    tbl(["ID", "Requirement"],
        [["FR-005.1", "Admin CRUD for: FX Clients, Banks, Counterparties, Currencies, Transaction/Transfer Types"],
         ["FR-005.2", "Bank accounts managed per-bank with Account Name (required) + Account Number"],
         ["FR-005.3", "Bank account selector shows searchable autocomplete with name + number"],
         ["FR-005.4", "CSV/Excel import for FX Clients (name, code, type) and Bank Accounts"],
         ["FR-005.5", "Global bank account import supporting fld_* legacy format with auto bank creation"]],
        w=[60, 405])
    sp()
    h2("FR-006: Reports")
    tbl(["ID", "Requirement"],
        [["FR-006.1", "8 report types: Deal Blotter, Settlement, Open Positions, Audit Trail, User Activity, Volume Summary, Client Activity, TMS"],
         ["FR-006.2", "Server-side pagination with sort for linear reports"],
         ["FR-006.3", "CSV and branded PDF export"],
         ["FR-006.4", "Admin-configurable role-based report permissions"],
         ["FR-006.5", "FX-Intercompany dual-line handling in Settlement/TMS reports"]],
        w=[60, 405])
    e.append(PageBreak())

    # 5
    h1("5. API Specification")
    h2("5.1 Authentication")
    tbl(["Method", "Endpoint", "Description"],
        [["POST", "/api/auth/register", "Create new user (admin only)"],
         ["POST", "/api/auth/login", "Authenticate, returns JWT"],
         ["PUT", "/api/auth/change-password", "Change current user password"]],
        w=[45, 150, 270])
    sp()
    h2("5.2 Deals")
    tbl(["Method", "Endpoint", "Description"],
        [["POST", "/api/deals", "Create deal ticket"],
         ["GET", "/api/deals", "List deals (filtered by role)"],
         ["GET", "/api/deals/treasury", "Treasury pending queue"],
         ["GET", "/api/deals/{id}", "Deal detail"],
         ["PUT", "/api/deals/{id}", "Edit returned deal"],
         ["POST", "/api/deals/{id}/confirm", "Treasury confirm"],
         ["POST", "/api/deals/{id}/return", "Treasury return"],
         ["POST", "/api/deals/{id}/cancel", "Trader cancel"],
         ["POST", "/api/deals/{id}/resubmit", "Trader resubmit"],
         ["POST", "/api/deals/{id}/proof", "Upload settlement proof"],
         ["DELETE", "/api/deals/{id}/proof/{pid}", "Delete proof"]],
        w=[45, 160, 260])
    sp()
    h2("5.3 Reference Data")
    tbl(["Method", "Endpoint", "Description"],
        [["GET/POST/PUT/DELETE", "/api/reference/{type}", "CRUD for companies, banks, currencies, etc."],
         ["GET/POST", "/api/reference/banks/{id}/accounts", "List/create bank accounts"],
         ["POST", "/api/reference/banks/{id}/accounts/import", "Per-bank CSV/Excel import"],
         ["POST", "/api/reference/bank-accounts/import", "Global multi-bank import (fld_* format)"],
         ["POST", "/api/reference/companies/import", "FX Client CSV/Excel import"]],
        w=[100, 195, 170])
    sp()
    h2("5.4 Reports")
    tbl(["Method", "Endpoint", "Description"],
        [["GET", "/api/reports/{type}?format=json", "Report data (paginated JSON)"],
         ["GET", "/api/reports/{type}?format=csv", "Full CSV export"],
         ["GET", "/api/reports/{type}?format=pdf", "Branded PDF export"],
         ["GET/PUT", "/api/reports/permissions", "Report permission config"]],
        w=[45, 190, 230])
    e.append(PageBreak())

    # 6
    h1("6. Data Models")
    h2("6.1 Deal Document")
    tbl(["Field", "Type", "Required", "Description"],
        [["id", "UUID", "Yes", "Unique identifier"],
         ["reference_number", "String", "Auto", "FX-YYYYMMDD-NNNN format"],
         ["client_name", "String", "Yes", "Client/company name"],
         ["transaction_type", "String", "Yes", "Buy or Sell"],
         ["transfer_type", "String", "Yes", "FX Crypto, FX Local, etc."],
         ["counterparty", "String", "No", "PJL Group entity (FX Local/Interco)"],
         ["buy_currency", "String", "Yes", "Currency code"],
         ["currency_amount", "Float", "Yes", "Principal amount"],
         ["rate", "Float", "Yes", "Exchange rate"],
         ["amount", "Float", "Yes", "Converted amount (currency_amount x rate)"],
         ["from_type", "String", "Yes", "bank or crypto"],
         ["from_network", "String", "Cond.", "SOLANA/ETHEREUM/TRON (if crypto)"],
         ["to_network", "String", "Cond.", "Destination network (if crypto)"],
         ["ours_network", "String", "Cond.", "Ours network (if crypto)"],
         ["status", "String", "Yes", "pending/confirmed/returned/cancelled"],
         ["settlement_proofs", "Array", "No", "List of proof objects"]],
        w=[80, 45, 35, 305])
    sp()
    h2("6.2 Bank Account Document")
    tbl(["Field", "Type", "Description"],
        [["id", "UUID", "Unique identifier"],
         ["bank_id", "UUID", "Foreign key to bank"],
         ["account_number", "String", "Bank account number"],
         ["account_name", "String", "Descriptive name (required)"],
         ["currency_code", "String", "PHP, USD, etc. (from import)"],
         ["account_type", "String", "SA, CA, etc. (from import)"],
         ["bank_address", "String", "Branch address (from import)"],
         ["account_alias", "String", "Short alias (from import)"]],
        w=[80, 45, 340])
    e.append(PageBreak())

    # 7
    h1("7. Security Requirements")
    tbl(["ID", "Requirement"],
        [["SEC-01", "All API endpoints require JWT authentication except /auth/login"],
         ["SEC-02", "Passwords hashed with bcrypt (work factor 12)"],
         ["SEC-03", "Role-based access enforced on every endpoint"],
         ["SEC-04", "File uploads validated for type and size (10MB max)"],
         ["SEC-05", "CORS configured for known frontend origin"],
         ["SEC-06", "All state-changing actions logged in audit trail"],
         ["SEC-07", "Environment variables used for all secrets (no hardcoded credentials)"],
         ["SEC-08", "Database credentials never exposed to frontend"]],
        w=[50, 415])
    e.append(PageBreak())

    # 8
    h1("8. User Interface Specifications")
    h2("8.1 Login Page")
    img("01_login.png", "Figure 8.1 - Login Page")
    h2("8.2 Dashboard")
    img("02_dashboard.png", "Figure 8.2 - Dashboard with summary cards and charts")
    h2("8.3 Deal Creation")
    img("04_new_deal.png", "Figure 8.3 - New Deal Form (top)")
    img("14_new_deal_bottom.png", "Figure 8.4 - New Deal Form (source/destination)")
    e.append(PageBreak())
    h2("8.4 My Deals")
    img("03_my_deals.png", "Figure 8.5 - My Deals with currency_amount and Last Action")
    h2("8.5 Deal Detail")
    img("05_deal_detail.png", "Figure 8.6 - Deal Detail Dialog")
    e.append(PageBreak())
    h2("8.6 Treasury Queue")
    img("06_treasury_queue.png", "Figure 8.7 - Treasury Deal Queue")
    h2("8.7 Reference Data")
    img("07_reference_data.png", "Figure 8.8 - Reference Data (FX Client)")
    img("08_banks.png", "Figure 8.9 - Banks with Accounts")
    e.append(PageBreak())
    h2("8.8 Reports")
    img("11_reports.png", "Figure 8.10 - Reports Page")
    h2("8.9 Audit Trail")
    img("12_audit_trail.png", "Figure 8.11 - Audit Trail")
    h2("8.10 System Administration")
    img("18_system_admin.png", "Figure 8.12 - System Admin Page")
    e.append(PageBreak())

    # 9
    h1("9. Deployment Architecture")
    h2("9.1 Environment Configuration")
    tbl(["Variable", "Location", "Purpose"],
        [["REACT_APP_BACKEND_URL", "frontend/.env", "API base URL for frontend"],
         ["MONGO_URL", "backend/.env", "MongoDB connection string"],
         ["DB_NAME", "backend/.env", "Database name"],
         ["DB_TYPE", "backend/.env", "mongodb or couchbase"],
         ["STORAGE_TYPE", "backend/.env", "emergent or s3"],
         ["S3_ENDPOINT / S3_ACCESS_KEY / etc.", "backend/.env", "S3-compatible storage config"],
         ["CB_CONNECTION_STRING / CB_USERNAME / etc.", "backend/.env", "Couchbase connection config"]],
        w=[120, 80, 265])
    sp()
    h2("9.2 Process Management")
    b("Backend and frontend are managed by Supervisor with automatic hot-reload. Backend runs on port 8001, frontend on port 3000, with Kubernetes ingress routing /api/* to backend.")
    e.append(PageBreak())

    # 10
    h1("10. Integration Points")
    tbl(["Integration", "Protocol", "Purpose", "Status"],
        [["MongoDB", "Motor (async)", "Primary database", "Active"],
         ["Couchbase Enterprise", "SDK 4.6 / N1QL", "Alternative enterprise DB", "Validated"],
         ["Emergent Object Storage", "HTTP API", "Settlement proof storage", "Active"],
         ["S3-Compatible (Huawei OBS / MinIO)", "boto3 / S3 API", "On-premise proof storage", "Validated"],
         ["ReportLab", "Python library", "PDF report generation", "Active"],
         ["openpyxl", "Python library", "Excel import parsing", "Active"]],
        w=[100, 70, 140, 155])


def srs_docx_content(doc):
    _title_page_docx(doc, "Software Requirements Specification", f"FX Trading Tracker Platform  |  Version {VER}")

    _dh(doc, "1. Introduction")
    doc.add_paragraph("This SRS defines the technical requirements for the FX Trading Tracker, a web-based platform for FX deal ticket management with multi-role workflow, settlement proofs, reports, and audit logging.")
    doc.add_page_break()

    _dh(doc, "2. System Architecture")
    doc.add_paragraph("Three-tier architecture: React SPA frontend, FastAPI REST backend, switchable MongoDB/Couchbase database with Emergent/S3 storage.")
    _dt(doc, ["Component", "Technology", "Responsibility"],
        [["Frontend SPA", "React 19, TailwindCSS, Shadcn/UI", "User interface, API calls"],
         ["API Server", "FastAPI, Uvicorn", "REST endpoints, JWT auth, business logic"],
         ["Database", "MongoDB (Motor) / Couchbase (SDK 4.6)", "Switchable document storage"],
         ["Storage", "Emergent / S3 (boto3)", "Settlement proof file storage"],
         ["Reports", "ReportLab, CSV", "PDF/CSV export with branded templates"]])
    doc.add_page_break()

    _dh(doc, "3. Technology Stack")
    _dh(doc, "3.1 Backend", 2)
    _dt(doc, ["Package", "Version", "Purpose"],
        [["FastAPI", "0.110.1", "REST API"],["Pydantic", "2.12.5", "Validation"],["Motor", "3.7.1", "MongoDB async"],
         ["Couchbase", "4.6.0", "Enterprise DB"],["boto3", "1.42.58", "S3 storage"],["ReportLab", "4.4.10", "PDF gen"],
         ["python-jose", "3.4.0", "JWT"],["bcrypt", "4.3.0", "Password hashing"]])
    _dh(doc, "3.2 Frontend", 2)
    _dt(doc, ["Package", "Version", "Purpose"],
        [["React", "19.0.0", "UI framework"],["React Router", "7.5.1", "Routing"],["TailwindCSS", "3.4.17", "CSS"],
         ["Shadcn/UI", "latest", "Components"],["Axios", "1.8.4", "HTTP"],["Recharts", "2.15.3", "Charts"]])
    doc.add_page_break()

    _dh(doc, "4. Functional Requirements")
    for sec, items in [
        ("FR-001: Authentication", ["JWT auth with 24h expiry", "RBAC (Trader/Treasury/Admin/Sysadmin)", "bcrypt password hashing"]),
        ("FR-002: Deal Management", ["Create deals with Buy/Sell, 6 transfer types", "Auto reference FX-YYYYMMDD-NNNN", "Crypto network selection (SOLANA/ETHEREUM/TRON)", "FX-Intercompany dual Ours"]),
        ("FR-003: Treasury", ["Pending queue with customizable columns", "Confirm/Return with mandatory remarks", "Proof requirement enforcement"]),
        ("FR-004: Reference Data", ["Admin CRUD for all reference entities", "Bank account searchable autocomplete", "CSV/Excel import with fld_* format support"]),
        ("FR-005: Reports", ["8 report types with server-side pagination", "CSV and branded PDF export", "Admin-configurable permissions"])]:
        _dh(doc, sec, 2)
        for i in items: doc.add_paragraph(i, style='List Bullet')
    doc.add_page_break()

    _dh(doc, "5. API Specification")
    _dt(doc, ["Method", "Endpoint", "Description"],
        [["POST", "/api/auth/login", "Authenticate, returns JWT"],
         ["POST", "/api/deals", "Create deal ticket"],
         ["GET", "/api/deals", "List deals"],["GET", "/api/deals/treasury", "Treasury queue"],
         ["POST", "/api/deals/{id}/confirm", "Confirm deal"],["POST", "/api/deals/{id}/return", "Return deal"],
         ["POST", "/api/deals/{id}/proof", "Upload proof"],
         ["GET", "/api/reports/{type}", "Report data (json/csv/pdf)"],
         ["POST", "/api/reference/bank-accounts/import", "Global bank account import"],
         ["POST", "/api/reference/companies/import", "FX Client import"]])
    doc.add_page_break()

    _dh(doc, "6. Data Models")
    _dh(doc, "6.1 Deal Document", 2)
    _dt(doc, ["Field", "Type", "Description"],
        [["reference_number", "String", "FX-YYYYMMDD-NNNN"],["client_name", "String", "Client name"],
         ["transaction_type", "String", "Buy/Sell"],["transfer_type", "String", "FX type"],
         ["currency_amount", "Float", "Principal"],["rate", "Float", "FX rate"],["amount", "Float", "Converted"],
         ["from_network", "String", "Crypto network (if applicable)"],
         ["status", "String", "pending/confirmed/returned/cancelled"]])
    doc.add_page_break()

    _dh(doc, "7. Security Requirements")
    _dt(doc, ["ID", "Requirement"],
        [["SEC-01", "JWT auth on all endpoints except login"],["SEC-02", "bcrypt password hashing"],
         ["SEC-03", "Role-based access enforcement"],["SEC-04", "File upload validation (10MB)"],
         ["SEC-05", "CORS configured"],["SEC-06", "All actions audit-logged"]])
    doc.add_page_break()

    _dh(doc, "8. User Interface Specifications")
    _di(doc, "01_login.png", "Figure 8.1 - Login Page")
    _di(doc, "02_dashboard.png", "Figure 8.2 - Dashboard")
    _di(doc, "04_new_deal.png", "Figure 8.3 - New Deal Form")
    _di(doc, "06_treasury_queue.png", "Figure 8.4 - Treasury Queue")
    _di(doc, "07_reference_data.png", "Figure 8.5 - Reference Data")
    _di(doc, "11_reports.png", "Figure 8.6 - Reports")
    _di(doc, "12_audit_trail.png", "Figure 8.7 - Audit Trail")
    _di(doc, "18_system_admin.png", "Figure 8.8 - System Admin")
    doc.add_page_break()

    _dh(doc, "9. Deployment Architecture")
    _dt(doc, ["Variable", "Purpose"],
        [["DB_TYPE", "mongodb or couchbase"],["STORAGE_TYPE", "emergent or s3"],
         ["MONGO_URL", "MongoDB connection"],["REACT_APP_BACKEND_URL", "Frontend API URL"]])

    _dh(doc, "10. Integration Points")
    _dt(doc, ["Integration", "Protocol", "Status"],
        [["MongoDB", "Motor async", "Active"],["Couchbase", "SDK 4.6", "Validated"],
         ["Emergent Storage", "HTTP", "Active"],["S3/Huawei OBS", "boto3", "Validated"],
         ["ReportLab", "Python", "Active"]])


# ══════════════════════════════════════════════════════════════════════════════
# 3. USER MANUAL (reuses existing generate_user_manual.py pattern)
# ══════════════════════════════════════════════════════════════════════════════
def manual_pdf_content(e, s):
    h1=lambda t: e.append(Paragraph(t, s["H1"]))
    h2=lambda t: e.append(Paragraph(t, s["H2"]))
    b=lambda t: e.append(Paragraph(t, s["Body"]))
    sp=lambda n=6: e.append(Spacer(1, n))
    note=lambda t: e.append(Paragraph(t, s["Note"]))
    code=lambda t: e.append(Paragraph(t, s["CodeBlk"]))
    bul=lambda t: e.append(Paragraph(t, s["BulletPt"], bulletText="\u2022"))
    img=lambda fn,cap=None: _pi(e, fn, cap, s)
    def tbl(hd, rows, w=None):
        t = Table([hd]+rows, colWidths=w, repeatRows=1); t.setStyle(_ts()); e.append(t); sp()

    _title_page_pdf(e, s, "User Manual", f"FX Trading Tracker Platform  |  Version {VER}")

    # TOC
    h1("Table of Contents")
    for t in ["1. Introduction & Roles","2. Getting Started","3. Dashboard","4. My Deals (Trader)",
              "5. New Deal Ticket","6. Deal Queue (Treasury)","7. Reference Data (Admin)",
              "8. User Management","9. Transactions & Audit Trail","10. Reports",
              "11. System Administration","12. Appendix"]:
        b(f"    {t}")
    e.append(PageBreak())

    # 1
    h1("1. Introduction & Roles")
    b("The FX Trading Tracker is a web-based platform for managing foreign exchange deal tickets. It supports the full deal lifecycle from creation through treasury processing.")
    sp()
    tbl(["Role", "Access"],
        [["Trader", "Create deals, upload client proofs, view own deals, reports"],
         ["Treasury", "Review/process deals, upload processor proofs, reports"],
         ["Admin", "Manage users, reference data, audit trail, report permissions, CSV imports"],
         ["System Admin", "Full admin + database reset, exports, statistics"]],
        w=[70, 395])
    e.append(PageBreak())

    # 2
    h1("2. Getting Started")
    h2("2.1 Logging In")
    b("Navigate to the application URL. Enter your Email and Password, then click Sign In.")
    img("01_login.png", "Figure 2.1 - Login Page")
    h2("2.2 Navigation")
    b("The sidebar provides role-based navigation. Traders: Dashboard, My Deals, New Deal, Reports. Treasury: Dashboard, Deal Queue, Reports. Admin: Dashboard, Reference Data, Users, Transactions, Audit Trail, Reports.")
    h2("2.3 Password Change")
    b("Click Change Password in the sidebar. Enter current and new password (min 4 chars).")
    e.append(PageBreak())

    # 3
    h1("3. Dashboard")
    img("02_dashboard.png", "Figure 3.1 - Dashboard")
    b("Summary cards show Total Deals, Pending, Confirmed, Returned. Date filters: Today, Yesterday, 7D, 30D, YTD, All Time. Charts: Deals Over Time and Status Distribution.")
    note("Traders see only their own data. Admin/Treasury see all deals.")
    e.append(PageBreak())

    # 4
    h1("4. My Deals (Trader)")
    img("03_my_deals.png", "Figure 4.1 - My Deals with Amount (currency) and Last Action")
    b("Columns: Reference, Client, Type, Pair, Amount (original currency amount with label), Rate, Deal Date, Status, Last Action. Use Filters/Export CSV.")
    sp()
    h2("4.1 Deal Detail")
    img("05_deal_detail.png", "Figure 4.2 - Deal Detail Dialog")
    b("Shows all deal fields, conversion summary, Ours details, settlement proofs, and deal history. Upload client proofs, cancel pending deals, or edit/resubmit returned deals.")
    e.append(PageBreak())

    # 5
    h1("5. New Deal Ticket")
    img("04_new_deal.png", "Figure 5.1 - New Deal Form (top)")
    tbl(["Field", "Required", "Notes"],
        [["Client Name", "Yes", "Free text"],["Transaction Type", "Yes", "Buy or Sell"],
         ["Transfer Type", "Yes", "See Appendix for types"],["Deal/Value Date", "Yes", "Date pickers"],
         ["Currency", "Yes", "Searchable dropdown"],["Currency Amount", "Yes", "Principal amount"],
         ["Rate", "Yes", "FX rate"],["Converted Amount", "Auto", "Amount x Rate"]],
        w=[80, 45, 340])
    sp()
    h2("5.1 Source & Destination")
    img("14_new_deal_bottom.png", "Figure 5.2 - Source/Destination/Ours sections")
    b("Each section supports <b>Bank</b> or <b>Crypto</b> mode. Bank: Company/Counterparty + Bank + Account (searchable autocomplete with name + number). Crypto: Wallet Address + <b>Network</b> (SOLANA/ETHEREUM/TRON, required).")
    b("For FX-Intercompany deals, two Ours sections appear: Selling Counterparty Ours and Buying Counterparty Ours.")
    e.append(PageBreak())

    # 6
    h1("6. Deal Queue (Treasury)")
    img("06_treasury_queue.png", "Figure 6.1 - Treasury Queue with Last Action column")
    tbl(["Tab", "Contents"],
        [["Pending", "Deals awaiting review"],["Returned", "Deals awaiting trader correction"],["Processed", "Confirmed and cancelled"]],
        w=[80, 385])
    b("Click <b>Review</b> to open deal. Enter Treasury Remarks, then <b>Confirm</b> (green) or <b>Return</b> (red). At least 1 proof required for confirmation.")
    e.append(PageBreak())

    # 7
    h1("7. Reference Data (Admin)")
    img("07_reference_data.png", "Figure 7.1 - FX Client tab with Import button")
    tbl(["Tab", "Description"],
        [["FX Client", "Client entities (import via CSV/Excel)"],["Banks", "Banks with SWIFT codes, account management"],
         ["Counterparties", "PJL Group entities (CLSC, PJ, Verite)"],["Transaction Types", "Buy / Sell"],
         ["Transfer Types", "FX Crypto, Local, Bank Deal, Intercompany, Corp Settlement, PDAX"],
         ["Currencies", "Fiat (31), Stablecoin (16), Crypto (18)"]],
        w=[80, 385])
    sp()
    h2("7.1 Bank Accounts")
    img("08_banks.png", "Figure 7.2 - Banks with Accounts button and Import Accounts CSV")
    b("Per-bank: Click <b>Accounts</b>, add with Name (required) + Number. Import via CSV/Excel (account_number, account_name).")
    b("Global: Click <b>Import Accounts CSV</b> on Banks tab. Supports legacy fld_* format — auto-matches fld_BankCode to banks, creates new banks if needed, persists currency_code, account_type, bank_address.")
    code("fld_BankAccountID,fld_BankCode,fld_AccountNo,fld_BranchAddress,fld_CurrencyCode,...")
    sp()
    h2("7.2 FX Client Import")
    b("On FX Client tab, click Import CSV/Excel. Columns: name (required), code (required), type (optional).")
    code("name,code,type\nAcme Trading,ACME,Customer")
    e.append(PageBreak())

    # 8
    h1("8. User Management")
    img("10_users.png", "Figure 8.1 - User Management")
    b("View/search users. Add User (name, email, password, role). Edit or delete via icons.")
    e.append(PageBreak())

    # 9
    h1("9. Transactions & Audit Trail")
    img("13_transactions.png", "Figure 9.1 - Transaction History")
    b("System-wide deal view for admins. Filter by status, client, currency, date.")
    sp()
    img("12_audit_trail.png", "Figure 9.2 - Audit Trail")
    b("Records every action: deal lifecycle, proofs, user management, reference data changes, imports. Filter by action, entity, user, date.")
    e.append(PageBreak())

    # 10
    h1("10. Reports")
    img("11_reports.png", "Figure 10.1 - Reports Page")
    tbl(["Report", "Description"],
        [["Deal Blotter", "Complete deal log"],["Settlement", "Deals by value date with bank details"],
         ["Open Positions", "Pending deals by pair"],["Audit Trail", "Full action history"],
         ["User Activity", "Actions per user"],["Volume Summary", "Counts by period"],
         ["Client Activity", "Per-client stats"],["TMS (SAP)", "21-column SAP format"]],
        w=[80, 385])
    b("Export: CSV or branded PDF. Admin controls permissions per role via Permissions button.")
    e.append(PageBreak())

    # 11
    h1("11. System Administration")
    img("18_system_admin.png", "Figure 11.1 - System Admin Page")
    note("Only accessible to sysadmin role.")
    b("<b>Database Statistics</b> — Record counts for all collections.")
    b("<b>Data Export</b> — Export any collection as CSV or JSON.")
    b("<b>Database Reset</b> — Clears deals, audit logs, counters. Retains users, reference data. Type 'RESET DATABASE' to confirm.")
    note("WARNING: Reset is irreversible.")
    e.append(PageBreak())

    # 12
    h1("12. Appendix")
    h2("Transfer Types")
    tbl(["Transfer Type", "Code", "Counterparty", "Destination", "Notes"],
        [["FX Crypto Conversion", "FX_CRYPTO", "No", "Yes", "Standard crypto"],
         ["FX Local", "FX_LOCAL", "Yes", "Yes", "Counterparty dropdown"],
         ["PDAX Withdrawal", "PDAX_WD", "No", "Yes", "PDAX-specific"],
         ["FX Bank Deal", "FX_BANK", "No", "Hidden", "No destination"],
         ["FX-Intercompany", "FX_INTERCO", "Yes", "Yes", "Dual Ours sections"],
         ["FX - Corporate Settlement", "FX_CORP_SETTLE", "Yes", "Yes", "Like FX Local"]],
        w=[95, 68, 58, 55, 189])
    sp()
    h2("Crypto Networks")
    tbl(["Network", "Blockchain"],
        [["SOLANA", "Solana"],["ETHEREUM", "Ethereum (ERC-20)"],["TRON", "TRON (TRC-20)"]],
        w=[80, 385])
    sp()
    h2("Status Workflow")
    b("Created → Pending → Confirmed | Returned | Cancelled")
    b("Returned → Edit → Resubmit → Pending (cycle)")


def manual_docx_content(doc):
    _title_page_docx(doc, "User Manual", f"FX Trading Tracker Platform  |  Version {VER}")

    _dh(doc, "1. Introduction & Roles")
    doc.add_paragraph("The FX Trading Tracker manages FX deal tickets with multi-role workflow, settlement proofs, reports, and audit logging.")
    _dt(doc, ["Role", "Access"],
        [["Trader", "Create deals, upload client proofs, reports"],["Treasury", "Review/process deals, processor proofs, reports"],
         ["Admin", "Users, reference data, audit trail, imports, reports"],["System Admin", "Full admin + DB reset/exports/stats"]])
    doc.add_page_break()

    _dh(doc, "2. Getting Started")
    _di(doc, "01_login.png", "Figure 2.1 - Login Page")
    doc.add_paragraph("Enter Email and Password, click Sign In. Sidebar shows role-based navigation.")
    doc.add_page_break()

    _dh(doc, "3. Dashboard")
    _di(doc, "02_dashboard.png", "Figure 3.1 - Dashboard")
    doc.add_paragraph("Summary cards, date filters (Today/7D/30D/YTD/All), and charts (Deals Over Time, Status Distribution).")
    doc.add_page_break()

    _dh(doc, "4. My Deals (Trader)")
    _di(doc, "03_my_deals.png", "Figure 4.1 - My Deals")
    doc.add_paragraph("Amount shows original currency amount with label. Last Action shows most recent history badge. Click eye icon for full deal detail.")
    _di(doc, "05_deal_detail.png", "Figure 4.2 - Deal Detail")
    doc.add_page_break()

    _dh(doc, "5. New Deal Ticket")
    _di(doc, "04_new_deal.png", "Figure 5.1 - New Deal Form")
    _dt(doc, ["Field", "Required", "Notes"],
        [["Client Name", "Yes", "Free text"],["Transaction Type", "Yes", "Buy/Sell"],["Transfer Type", "Yes", "See Appendix"],
         ["Currency", "Yes", "Searchable"],["Amount", "Yes", "Principal"],["Rate", "Yes", "FX rate"]])
    _dh(doc, "5.1 Source/Destination/Ours", 2)
    _di(doc, "14_new_deal_bottom.png", "Figure 5.2 - Source/Destination sections")
    doc.add_paragraph("Bank mode: Company/Counterparty + Bank + Account (searchable). Crypto mode: Wallet + Network (SOLANA/ETHEREUM/TRON).")
    doc.add_page_break()

    _dh(doc, "6. Deal Queue (Treasury)")
    _di(doc, "06_treasury_queue.png", "Figure 6.1 - Treasury Queue")
    doc.add_paragraph("Tabs: Pending, Returned, Processed. Click Review, enter remarks, Confirm or Return. Min 1 proof required for confirmation.")
    doc.add_page_break()

    _dh(doc, "7. Reference Data (Admin)")
    _di(doc, "07_reference_data.png", "Figure 7.1 - FX Client tab")
    _di(doc, "08_banks.png", "Figure 7.2 - Banks with Import Accounts CSV")
    doc.add_paragraph("6 tabs: FX Client, Banks, Counterparties, Transaction/Transfer Types, Currencies. CSV/Excel import for FX Clients and Bank Accounts (including legacy fld_* format with auto bank creation).")
    doc.add_page_break()

    _dh(doc, "8. User Management")
    _di(doc, "10_users.png", "Figure 8.1 - Users")
    doc.add_page_break()

    _dh(doc, "9. Transactions & Audit Trail")
    _di(doc, "13_transactions.png", "Figure 9.1 - Transactions")
    _di(doc, "12_audit_trail.png", "Figure 9.2 - Audit Trail")
    doc.add_page_break()

    _dh(doc, "10. Reports")
    _di(doc, "11_reports.png", "Figure 10.1 - Reports")
    _dt(doc, ["Report", "Description"],
        [["Deal Blotter", "Complete log"],["Settlement", "By value date"],["Open Positions", "Pending by pair"],
         ["Audit Trail", "Actions"],["User Activity", "Per user"],["Volume Summary", "By period"],
         ["Client Activity", "Per client"],["TMS (SAP)", "21-column SAP"]])
    doc.add_page_break()

    _dh(doc, "11. System Administration")
    _di(doc, "18_system_admin.png", "Figure 11.1 - System Admin")
    _dn(doc, "Only accessible to sysadmin role.")
    doc.add_paragraph("DB Statistics, Data Export (CSV/JSON), Database Reset (clears deals/audit, retains users/ref data).")
    doc.add_page_break()

    _dh(doc, "12. Appendix: Transfer Types & Networks")
    _dt(doc, ["Transfer Type", "Code", "Counterparty", "Destination"],
        [["FX Crypto Conversion", "FX_CRYPTO", "No", "Yes"],["FX Local", "FX_LOCAL", "Yes", "Yes"],
         ["FX Bank Deal", "FX_BANK", "No", "Hidden"],["FX-Intercompany", "FX_INTERCO", "Yes", "Yes (dual Ours)"],
         ["FX - Corporate Settlement", "FX_CORP_SETTLE", "Yes", "Yes"],["PDAX Withdrawal", "PDAX_WD", "No", "Yes"]])
    doc.add_paragraph("Crypto Networks: SOLANA, ETHEREUM, TRON")
    doc.add_paragraph("Status Workflow: Created → Pending → Confirmed | Returned | Cancelled. Returned → Edit → Resubmit → Pending.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    print("=== Generating BRD ===")
    _build_pdf(f"{OUT}/FX_Trading_Tracker_BRD.pdf", "Business Requirements Document", brd_pdf_content)
    _build_docx(f"{OUT}/FX_Trading_Tracker_BRD.docx", "Business Requirements Document", brd_docx_content)

    print("\n=== Generating SRS ===")
    _build_pdf(f"{OUT}/FX_Trading_Tracker_SRS.pdf", "Software Requirements Specification", srs_pdf_content)
    _build_docx(f"{OUT}/FX_Trading_Tracker_SRS.docx", "Software Requirements Specification", srs_docx_content)

    print("\n=== Generating User Manual ===")
    _build_pdf(f"{OUT}/FX_Trading_Tracker_User_Manual.pdf", "User Manual", manual_pdf_content)
    _build_docx(f"{OUT}/FX_Trading_Tracker_User_Manual.docx", "User Manual", manual_docx_content)

    print(f"\nAll documents generated in {OUT}/")
