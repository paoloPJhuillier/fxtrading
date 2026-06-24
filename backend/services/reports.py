"""
Report generation engine — CSV + PDF for all FX trading reports.

Branding:
  Primary: #08263e (dark navy), #ec474e (red accent)
  Secondary: #518dca (blue), #f1f2f2 (light gray rows)
"""

import io
import csv
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Brand colors
C_NAVY = colors.HexColor("#08263e")
C_RED = colors.HexColor("#ec474e")
C_BLUE = colors.HexColor("#518dca")
C_GRAY = colors.HexColor("#f1f2f2")
C_WHITE = colors.white
C_BLACK = colors.black


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("ReportTitle", parent=ss["Title"], fontSize=18, textColor=C_NAVY, spaceAfter=2))
    ss.add(ParagraphStyle("ReportSub", parent=ss["Normal"], fontSize=9, textColor=C_BLUE, spaceAfter=12))
    ss.add(ParagraphStyle("SectionHead", parent=ss["Heading2"], fontSize=12, textColor=C_NAVY, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("CellText", parent=ss["Normal"], fontSize=7, leading=9))
    ss.add(ParagraphStyle("SummaryLabel", parent=ss["Normal"], fontSize=9, textColor=C_NAVY, alignment=TA_RIGHT))
    ss.add(ParagraphStyle("SummaryValue", parent=ss["Normal"], fontSize=9, textColor=C_RED, alignment=TA_LEFT))
    return ss


def _table_style(col_count):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 6.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ])


def _header_footer(canvas, doc, title, date_range):
    canvas.saveState()
    # Top bar
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, doc.pagesize[1] - 12 * mm, doc.pagesize[0], 12 * mm, fill=True, stroke=False)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(15 * mm, doc.pagesize[1] - 8 * mm, "FX Trading Tracker")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, doc.pagesize[1] - 8 * mm, f"{title}  |  {date_range}")
    # Red accent line
    canvas.setStrokeColor(C_RED)
    canvas.setLineWidth(1.5)
    canvas.line(0, doc.pagesize[1] - 12 * mm, doc.pagesize[0], doc.pagesize[1] - 12 * mm)
    # Footer
    canvas.setFillColor(C_NAVY)
    canvas.setFont("Helvetica", 6)
    canvas.drawString(15 * mm, 8 * mm, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    canvas.drawRightString(doc.pagesize[0] - 15 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _build_pdf(title, date_range, elements, landscape_mode=True):
    buf = io.BytesIO()
    pagesize = landscape(A4) if landscape_mode else A4
    doc = SimpleDocTemplate(buf, pagesize=pagesize,
                            topMargin=18 * mm, bottomMargin=15 * mm,
                            leftMargin=12 * mm, rightMargin=12 * mm)

    def on_page(canvas, doc_):
        _header_footer(canvas, doc_, title, date_range)

    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
    buf.seek(0)
    return buf


def _build_csv(headers, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    buf.seek(0)
    return buf.getvalue()


def _fmt_num(v, decimals=2):
    if v is None:
        return ""
    try:
        return f"{float(v):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(v)


def _fmt_date(v):
    if not v:
        return ""
    return str(v)[:10]


# ── Report 1: Deal Blotter ──────────────────────────────────────────────────

def deal_blotter_csv(deals):
    headers = ["Ref#", "Date", "Value Date", "Client", "Txn Type", "Transfer Type",
               "Buy CCY", "Sell CCY", "Amount", "Rate", "Settlement Amt",
               "Status", "Created By", "Processed By", "Remarks"]
    rows = []
    for d in deals:
        rows.append([
            d.get("reference_number", ""), _fmt_date(d.get("deal_date")), _fmt_date(d.get("value_date")),
            d.get("client_name", ""), d.get("transaction_type", ""), d.get("transfer_type", ""),
            d.get("buy_currency", ""), d.get("sell_currency", ""),
            _fmt_num(d.get("currency_amount")), _fmt_num(d.get("rate"), 4), _fmt_num(d.get("amount")),
            d.get("status", ""), d.get("created_by_name", ""), d.get("processed_by_name", ""),
            d.get("remarks", ""),
        ])
    return _build_csv(headers, rows)


def deal_blotter_pdf(deals, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Deal Blotter", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Total Deals: {len(deals)}", ss["ReportSub"]))

    headers = ["Ref#", "Deal Date", "Value Date", "Client", "Type", "Buy", "Sell",
               "CCY Amt", "Rate", "Settle Amt", "Status", "Trader"]
    data = [headers]
    for d in deals:
        data.append([
            d.get("reference_number", ""), _fmt_date(d.get("deal_date")), _fmt_date(d.get("value_date")),
            d.get("client_name", "")[:20], d.get("transaction_type", ""),
            d.get("buy_currency", ""), d.get("sell_currency", ""),
            _fmt_num(d.get("currency_amount")), _fmt_num(d.get("rate"), 4),
            _fmt_num(d.get("amount")), d.get("status", "").upper(),
            d.get("created_by_name", "")[:15],
        ])

    col_widths = [55, 52, 52, 75, 35, 30, 30, 55, 42, 55, 48, 60]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)

    # Summary
    total_vol = sum(float(d.get("amount", 0) or 0) for d in deals)
    by_status = {}
    for d in deals:
        s = d.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    elems.append(Spacer(1, 10))
    summary = f"Total Settlement Volume: {_fmt_num(total_vol)}  |  "
    summary += "  |  ".join(f"{s.title()}: {c}" for s, c in sorted(by_status.items()))
    elems.append(Paragraph(summary, ss["SummaryLabel"]))

    return _build_pdf("Deal Blotter", date_range, elems)


# ── Report 2: Settlement Report ─────────────────────────────────────────────

def settlement_csv(deals):
    headers = ["Value Date", "Ref#", "Client", "Buy CCY", "Sell CCY", "CCY Amount",
               "Settlement Amt", "Source Bank", "Source Acct", "Dest Bank", "Dest Acct",
               "Proofs Uploaded", "Status"]
    rows = []
    for d in deals:
        proofs = len(d.get("settlement_proofs", []))
        rows.append([
            _fmt_date(d.get("value_date")), d.get("reference_number", ""),
            d.get("client_name", ""), d.get("buy_currency", ""), d.get("sell_currency", ""),
            _fmt_num(d.get("currency_amount")), _fmt_num(d.get("amount")),
            d.get("from_bank", ""), d.get("from_account_num", ""),
            d.get("to_bank", ""), d.get("to_account_num", ""),
            proofs, d.get("status", ""),
        ])
    return _build_csv(headers, rows)


def settlement_pdf(deals, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Settlement Report", ss["ReportTitle"]))
    elems.append(Paragraph(f"Value Date Range: {date_range}  |  Deals: {len(deals)}", ss["ReportSub"]))

    headers = ["Value Date", "Ref#", "Client", "Buy", "Sell", "CCY Amt", "Settle Amt",
               "From Bank", "To Bank", "Proofs", "Status"]
    data = [headers]
    for d in deals:
        proofs = len(d.get("settlement_proofs", []))
        data.append([
            _fmt_date(d.get("value_date")), d.get("reference_number", ""),
            d.get("client_name", "")[:18], d.get("buy_currency", ""), d.get("sell_currency", ""),
            _fmt_num(d.get("currency_amount")), _fmt_num(d.get("amount")),
            d.get("from_bank", "")[:12], d.get("to_bank", "")[:12],
            str(proofs), d.get("status", "").upper(),
        ])

    col_widths = [52, 58, 70, 30, 30, 55, 55, 55, 55, 32, 48]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)

    total = sum(float(d.get("amount", 0) or 0) for d in deals)
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"Total Settlement Amount: {_fmt_num(total)}", ss["SummaryLabel"]))
    return _build_pdf("Settlement Report", date_range, elems)


# ── Report 3: Open Positions ────────────────────────────────────────────────

def open_positions_csv(positions):
    headers = ["Currency Pair", "# Deals", "Total Buy Amount", "Total Sell Amount", "Net Position"]
    rows = [[p["pair"], p["count"], _fmt_num(p["buy_total"]), _fmt_num(p["sell_total"]), _fmt_num(p["net"])] for p in positions]
    return _build_csv(headers, rows)


def open_positions_pdf(positions, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Outstanding Open Positions", ss["ReportTitle"]))
    elems.append(Paragraph(f"As of: {date_range}  |  Pending deals only", ss["ReportSub"]))

    headers = ["Currency Pair", "# Deals", "Total Buy Amount", "Total Sell Amount", "Net Position"]
    data = [headers]
    for p in positions:
        data.append([p["pair"], str(p["count"]), _fmt_num(p["buy_total"]), _fmt_num(p["sell_total"]), _fmt_num(p["net"])])

    col_widths = [100, 60, 100, 100, 100]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)
    return _build_pdf("Open Positions", date_range, elems, landscape_mode=False)


# ── Report 4: Audit Trail ───────────────────────────────────────────────────

def audit_trail_csv(logs):
    headers = ["Timestamp", "Action", "Entity", "Reference", "User", "Role", "Details"]
    rows = []
    for l in logs:
        rows.append([
            l.get("created_at", "")[:19], l.get("action", ""), l.get("entity_type", ""),
            l.get("entity_ref", ""), l.get("user_name", ""), l.get("user_role", ""),
            l.get("details", ""),
        ])
    return _build_csv(headers, rows)


def audit_trail_pdf(logs, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Transaction Audit Trail", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Entries: {len(logs)}", ss["ReportSub"]))

    headers = ["Timestamp", "Action", "Entity", "Reference", "User", "Role", "Details"]
    data = [headers]
    for l in logs:
        data.append([
            l.get("created_at", "")[:19], l.get("action", ""),
            l.get("entity_type", ""), l.get("entity_ref", "")[:18],
            l.get("user_name", "")[:15], l.get("user_role", ""),
            l.get("details", "")[:50],
        ])

    col_widths = [75, 65, 45, 70, 65, 45, 180]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)
    return _build_pdf("Audit Trail", date_range, elems)


# ── Report 5: User Activity ─────────────────────────────────────────────────

def user_activity_csv(activities):
    headers = ["User", "Role", "Deals Created", "Deals Processed", "Deals Returned",
               "Proofs Uploaded", "Total Actions"]
    rows = []
    for a in activities:
        rows.append([a["user_name"], a["role"], a["created"], a["processed"],
                     a["returned"], a["proofs"], a["total"]])
    return _build_csv(headers, rows)


def user_activity_pdf(activities, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("User Activity Report", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Users: {len(activities)}", ss["ReportSub"]))

    headers = ["User", "Role", "Created", "Processed", "Returned", "Proofs", "Total"]
    data = [headers]
    for a in activities:
        data.append([a["user_name"], a["role"], str(a["created"]), str(a["processed"]),
                     str(a["returned"]), str(a["proofs"]), str(a["total"])])

    col_widths = [120, 60, 55, 60, 55, 50, 50]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)
    return _build_pdf("User Activity", date_range, elems, landscape_mode=False)


# ── Report 6: Volume Summary ────────────────────────────────────────────────

def volume_summary_csv(summary):
    headers = ["Period", "# Deals", "Total Volume", "Avg Deal Size", "Confirmed", "Pending", "Returned", "Cancelled"]
    rows = []
    for s in summary:
        rows.append([s["period"], s["count"], _fmt_num(s["volume"]), _fmt_num(s["avg"]),
                     s["confirmed"], s["pending"], s["returned"], s["cancelled"]])
    return _build_csv(headers, rows)


def volume_summary_pdf(summary, date_range, group_by):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Volume Summary Report", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Grouped by: {group_by}", ss["ReportSub"]))

    headers = ["Period", "# Deals", "Total Volume", "Avg Deal Size", "Confirmed", "Pending", "Returned", "Cancelled"]
    data = [headers]
    for s in summary:
        data.append([s["period"], str(s["count"]), _fmt_num(s["volume"]), _fmt_num(s["avg"]),
                     str(s["confirmed"]), str(s["pending"]), str(s["returned"]), str(s["cancelled"])])

    col_widths = [70, 45, 70, 65, 50, 45, 50, 50]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)

    total_vol = sum(s["volume"] for s in summary)
    total_deals = sum(s["count"] for s in summary)
    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"Grand Total: {total_deals} deals  |  Volume: {_fmt_num(total_vol)}", ss["SummaryLabel"]))
    return _build_pdf("Volume Summary", date_range, elems, landscape_mode=False)


# ── Report 7: Client Activity ───────────────────────────────────────────────

def client_activity_csv(clients):
    headers = ["Client", "# Deals", "Total Volume", "Avg Deal Size", "Currency Pairs", "Last Deal Date"]
    rows = []
    for c in clients:
        rows.append([c["client"], c["count"], _fmt_num(c["volume"]), _fmt_num(c["avg"]),
                     c["pairs"], _fmt_date(c["last_deal"])])
    return _build_csv(headers, rows)


def client_activity_pdf(clients, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("Client Activity Report", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Clients: {len(clients)}", ss["ReportSub"]))

    headers = ["Client", "# Deals", "Total Volume", "Avg Deal Size", "Currency Pairs", "Last Deal"]
    data = [headers]
    for c in clients:
        data.append([c["client"][:25], str(c["count"]), _fmt_num(c["volume"]),
                     _fmt_num(c["avg"]), c["pairs"][:30], _fmt_date(c["last_deal"])])

    col_widths = [100, 45, 70, 65, 110, 55]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)
    return _build_pdf("Client Activity", date_range, elems, landscape_mode=False)


# ── Report 8: TMS (SAP Mass Upload) ─────────────────────────────────────────

def tms_pdf(rows, date_range):
    ss = _styles()
    elems = []
    elems.append(Paragraph("TMS Report — SAP Mass Upload", ss["ReportTitle"]))
    elems.append(Paragraph(f"Period: {date_range}  |  Entries: {len(rows)}", ss["ReportSub"]))

    headers = ["Buy/Trade", "Transfer", "From Co", "From Bank", "To Co", "To Bank",
               "Buy Curr", "Sell Curr", "Buy Amt", "Sell Amt", "Ref#", "FX Partner", "Rate", "Status", "Maker"]
    data = [headers]
    for r in rows:
        data.append([
            r.get("buy_or_trade", ""), r.get("type_of_transfer", "")[:12],
            r.get("from_co", "")[:15], r.get("from_bank", "")[:10],
            r.get("to_co", "")[:15], r.get("to_bank", "")[:10],
            r.get("buy_curr", ""), r.get("sell_curr", ""),
            _fmt_num(r.get("buy_fx_amt")), _fmt_num(r.get("sell_fx_amt")),
            r.get("ref_no", ""), r.get("fx_partner", "")[:15],
            _fmt_num(r.get("rate"), 4), r.get("status", "").upper(),
            r.get("maker", "")[:12],
        ])

    col_widths = [35, 45, 52, 42, 52, 42, 30, 30, 48, 48, 60, 52, 38, 38, 45]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_table_style(len(headers)))
    elems.append(t)
    return _build_pdf("TMS Report", date_range, elems)
