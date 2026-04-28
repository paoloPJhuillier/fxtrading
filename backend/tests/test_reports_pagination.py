"""Iter 23 — Server-side pagination, sort, debounced search on row-level reports.

Covers:
- Row-level reports (deal-blotter, settlement, audit-trail) with page/limit/sort_by/sort_dir
- CSV/PDF still return full dataset (no pagination)
- Aggregation reports (open-positions, volume-summary, client-activity, user-activity)
  unchanged: no page/pages fields
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fx-deal-queue.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@fxtracker.com", "password": "Admin@123"}
TRADER = {"email": "trader@fxtracker.com", "password": "Trader@123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers():
    return {"Authorization": f"Bearer {_login(ADMIN)}"}


@pytest.fixture(scope="module")
def trader_headers():
    return {"Authorization": f"Bearer {_login(TRADER)}"}


# ---------------- Deal Blotter ----------------
class TestDealBlotterPagination:
    def test_page1_limit5(self, admin_headers):
        r = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 1, "limit": 5}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("rows", "total", "page", "pages"):
            assert k in d, f"missing key {k}"
        assert d["page"] == 1
        assert len(d["rows"]) <= 5
        if d["total"] >= 5:
            assert len(d["rows"]) == 5
        assert d["pages"] == ((d["total"] + 4) // 5 if d["total"] > 0 else 1)

    def test_page2_different_rows(self, admin_headers):
        r1 = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 1, "limit": 5}, headers=admin_headers, timeout=30)
        r2 = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 2, "limit": 5}, headers=admin_headers, timeout=30)
        assert r1.status_code == 200 and r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d2["page"] == 2
        if d1["total"] > 5:
            ids1 = {row.get("reference") or row.get("ref") or row.get("id") or str(row) for row in d1["rows"]}
            ids2 = {row.get("reference") or row.get("ref") or row.get("id") or str(row) for row in d2["rows"]}
            assert ids1 != ids2, "page 2 returned same rows as page 1"

    def test_server_side_sort_amount_desc(self, admin_headers):
        r = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 1, "limit": 10, "sort_by": "amount", "sort_dir": "desc"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        rows = r.json()["rows"]
        amts = [float(row.get("amount", 0) or 0) for row in rows]
        assert amts == sorted(amts, reverse=True), f"not desc-sorted by amount: {amts}"

    def test_server_side_sort_amount_asc(self, admin_headers):
        r = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 1, "limit": 10, "sort_by": "amount", "sort_dir": "asc"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        rows = r.json()["rows"]
        amts = [float(row.get("amount", 0) or 0) for row in rows]
        assert amts == sorted(amts), f"not asc-sorted by amount: {amts}"

    def test_csv_full_dataset(self, admin_headers):
        # Get JSON total first
        rj = requests.get(f"{API}/reports/deal-blotter", params={"format": "json", "page": 1, "limit": 5}, headers=admin_headers, timeout=30)
        total = rj.json()["total"]
        rc = requests.get(f"{API}/reports/deal-blotter", params={"format": "csv"}, headers=admin_headers, timeout=60)
        assert rc.status_code == 200
        assert "text/csv" in rc.headers.get("content-type", "")
        # Count data rows (subtract header)
        lines = [ln for ln in rc.text.splitlines() if ln.strip()]
        data_lines = max(0, len(lines) - 1)
        assert data_lines >= total or data_lines == total, f"CSV had {data_lines} data rows, JSON total={total}"

    def test_pdf_returns_full(self, admin_headers):
        r = requests.get(f"{API}/reports/deal-blotter", params={"format": "pdf"}, headers=admin_headers, timeout=60)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF"


# ---------------- Settlement ----------------
class TestSettlementPagination:
    def test_page1_limit10(self, admin_headers):
        r = requests.get(f"{API}/reports/settlement", params={"format": "json", "page": 1, "limit": 10}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("rows", "total", "page", "pages"):
            assert k in d
        assert d["page"] == 1
        assert len(d["rows"]) <= 10

    def test_from_bank_filter(self, admin_headers):
        r = requests.get(f"{API}/reports/settlement", params={"format": "json", "page": 1, "limit": 50, "from_bank": "JPMC"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        # All rows must contain JPMC in from_bank (case-insensitive)
        for row in d["rows"]:
            fb = (row.get("from_bank") or "").lower()
            assert "jpmc" in fb or fb == "", f"row from_bank '{fb}' missing JPMC"

    def test_csv_no_pagination(self, admin_headers):
        r = requests.get(f"{API}/reports/settlement", params={"format": "csv"}, headers=admin_headers, timeout=60)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")


# ---------------- Audit Trail (admin only) ----------------
class TestAuditTrailPagination:
    def test_page1_limit10(self, admin_headers):
        r = requests.get(f"{API}/reports/audit-trail", params={"format": "json", "page": 1, "limit": 10}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("rows", "total", "page", "pages"):
            assert k in d
        assert d["page"] == 1
        assert len(d["rows"]) <= 10

    def test_user_filter(self, admin_headers):
        r = requests.get(f"{API}/reports/audit-trail", params={"format": "json", "page": 1, "limit": 50, "user_name": "John"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for row in d["rows"]:
            un = (row.get("user_name") or "").lower()
            assert "john" in un, f"row user_name '{un}' missing john"

    def test_trader_forbidden(self, trader_headers):
        r = requests.get(f"{API}/reports/audit-trail", params={"format": "json", "page": 1, "limit": 5}, headers=trader_headers, timeout=30)
        assert r.status_code == 403


# ---------------- Aggregation reports (no pagination expected) ----------------
class TestAggregationReports:
    def test_volume_summary_no_pagination(self, admin_headers):
        r = requests.get(f"{API}/reports/volume-summary", params={"format": "json"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "rows" in d
        # Aggregation reports must NOT have page/pages
        assert "page" not in d, "volume-summary should not return page"
        assert "pages" not in d, "volume-summary should not return pages"

    def test_client_activity_filter(self, admin_headers):
        r = requests.get(f"{API}/reports/client-activity", params={"format": "json", "client": "Test"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "rows" in d
        assert "page" not in d
        for row in d["rows"]:
            cn = (row.get("client_name") or row.get("client") or "").lower()
            assert "test" in cn, f"row client '{cn}' missing test"

    def test_open_positions_snapshot(self, admin_headers):
        r = requests.get(f"{API}/reports/open-positions", params={"format": "json"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "rows" in d
        assert "page" not in d, "open-positions is a snapshot - no page"
        assert "pages" not in d

    def test_user_activity_no_pagination(self, admin_headers):
        r = requests.get(f"{API}/reports/user-activity", params={"format": "json"}, headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "rows" in d
        assert "page" not in d
