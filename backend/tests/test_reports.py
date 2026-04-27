"""Tests for Reports feature: CSV + PDF export for 7 report types."""

import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

TRADER = {"email": "trader@fxtracker.com", "password": "Trader@123"}
ADMIN = {"email": "admin@fxtracker.com", "password": "Admin@123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text}"
    body = r.json()
    return body.get("token") or body.get("access_token")


@pytest.fixture(scope="session")
def trader_token():
    return _login(TRADER)


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ── Deal Blotter ─────────────────────────────────────────────
class TestDealBlotter:
    def test_csv(self, admin_token):
        r = requests.get(f"{API}/reports/deal-blotter?format=csv", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "attachment" in r.headers.get("content-disposition", "")
        assert b"Ref#" in r.content or b"Client" in r.content

    def test_pdf(self, admin_token):
        r = requests.get(f"{API}/reports/deal-blotter?format=pdf", headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:4] == b"%PDF"

    def test_filter_status(self, admin_token):
        r = requests.get(f"{API}/reports/deal-blotter?format=csv&status=pending", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        import csv as _csv, io as _io
        reader = _csv.reader(_io.StringIO(r.text))
        rows = list(reader)
        if len(rows) > 1:
            header = rows[0]
            idx = header.index("Status")
            for row in rows[1:]:
                assert row[idx] == "pending", f"Expected pending, got {row[idx]}"

    def test_date_range(self, admin_token):
        r = requests.get(
            f"{API}/reports/deal-blotter?format=csv&date_from=2026-01-01&date_to=2026-12-31",
            headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")


# ── Settlement Report ─────────────────────────────────────────
class TestSettlement:
    def test_csv(self, admin_token):
        r = requests.get(f"{API}/reports/settlement?format=csv", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert r.text.startswith("Value Date") or "Value Date" in r.text

    def test_pdf(self, admin_token):
        r = requests.get(f"{API}/reports/settlement?format=pdf", headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"


# ── Open Positions ────────────────────────────────────────────
class TestOpenPositions:
    def test_csv(self, admin_token):
        r = requests.get(f"{API}/reports/open-positions?format=csv", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "Currency Pair" in r.text

    def test_pdf(self, admin_token):
        r = requests.get(f"{API}/reports/open-positions?format=pdf", headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"


# ── Audit Trail (admin only) ──────────────────────────────────
class TestAuditTrail:
    def test_csv_admin(self, admin_token):
        r = requests.get(f"{API}/reports/audit-trail?format=csv", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "Timestamp" in r.text

    def test_pdf_admin(self, admin_token):
        r = requests.get(f"{API}/reports/audit-trail?format=pdf", headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"

    def test_trader_forbidden(self, trader_token):
        r = requests.get(f"{API}/reports/audit-trail?format=csv", headers=_h(trader_token), timeout=30)
        assert r.status_code == 403, f"Expected 403 for trader; got {r.status_code}"


# ── User Activity (admin only) ────────────────────────────────
class TestUserActivity:
    def test_csv_admin(self, admin_token):
        r = requests.get(f"{API}/reports/user-activity?format=csv", headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "User" in r.text

    def test_trader_forbidden(self, trader_token):
        r = requests.get(f"{API}/reports/user-activity?format=csv", headers=_h(trader_token), timeout=30)
        assert r.status_code == 403


# ── Volume Summary ────────────────────────────────────────────
class TestVolumeSummary:
    def test_daily(self, admin_token):
        r = requests.get(f"{API}/reports/volume-summary?format=csv&group_by=daily",
                         headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "Period" in r.text

    def test_monthly(self, admin_token):
        r = requests.get(f"{API}/reports/volume-summary?format=csv&group_by=monthly",
                         headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "Period" in r.text

    def test_pdf(self, admin_token):
        r = requests.get(f"{API}/reports/volume-summary?format=pdf",
                         headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"


# ── Client Activity ───────────────────────────────────────────
class TestClientActivity:
    def test_csv(self, admin_token):
        r = requests.get(f"{API}/reports/client-activity?format=csv",
                         headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
        assert "Client" in r.text

    def test_pdf(self, admin_token):
        r = requests.get(f"{API}/reports/client-activity?format=pdf",
                         headers=_h(admin_token), timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"


# ── Auth ──────────────────────────────────────────────────────
class TestAuthRequired:
    def test_no_token(self):
        r = requests.get(f"{API}/reports/deal-blotter?format=csv", timeout=15)
        assert r.status_code in (401, 403)
