"""Tests for Report Permissions feature (iter 22).
Covers GET/PUT /api/reports/permissions, _check_report_access() guard,
and restores defaults at the end.
"""
import os
import pytest
import requests


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")


BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

TRADER = {"email": "trader@fxtracker.com", "password": "Trader@123"}
TREASURY = {"email": "treasury@fxtracker.com", "password": "Treasury@123"}
ADMIN = {"email": "admin@fxtracker.com", "password": "Admin@123"}

DEFAULT_PERMS = {
    "deal-blotter":    {"trader": True,  "treasury": True,  "admin": True},
    "settlement":      {"trader": True,  "treasury": True,  "admin": True},
    "open-positions":  {"trader": True,  "treasury": True,  "admin": True},
    "audit-trail":     {"trader": False, "treasury": False, "admin": True},
    "user-activity":   {"trader": False, "treasury": False, "admin": True},
    "volume-summary":  {"trader": True,  "treasury": True,  "admin": True},
    "client-activity": {"trader": True,  "treasury": True,  "admin": True},
}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed {r.status_code}: {r.text}"
    body = r.json()
    return body.get("token") or body.get("access_token")


@pytest.fixture(scope="session")
def trader_token():
    return _login(TRADER)


@pytest.fixture(scope="session")
def treasury_token():
    return _login(TREASURY)


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module", autouse=True)
def restore_defaults(admin_token):
    """Ensure defaults are in place before and after the module."""
    requests.put(f"{API}/reports/permissions",
                 headers=_h(admin_token),
                 json={"permissions": DEFAULT_PERMS}, timeout=15)
    yield
    requests.put(f"{API}/reports/permissions",
                 headers=_h(admin_token),
                 json={"permissions": DEFAULT_PERMS}, timeout=15)


# ── GET /api/reports/permissions ─────────────────────────────
class TestGetPermissions:
    def test_admin_sees_all_roles(self, admin_token):
        r = requests.get(f"{API}/reports/permissions", headers=_h(admin_token), timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert "permissions" in body
        perms = body["permissions"]
        # admin sees full matrix
        for rid in DEFAULT_PERMS:
            assert rid in perms
            for role in ("trader", "treasury", "admin"):
                assert role in perms[rid], f"Admin should see role {role} for {rid}"
        # values match defaults
        assert perms["audit-trail"]["trader"] is False
        assert perms["audit-trail"]["admin"] is True
        assert perms["deal-blotter"]["trader"] is True

    def test_trader_sees_only_own_role(self, trader_token):
        r = requests.get(f"{API}/reports/permissions", headers=_h(trader_token), timeout=15)
        assert r.status_code == 200
        perms = r.json()["permissions"]
        # trader should only have trader entries
        assert perms["audit-trail"].get("trader") is False
        assert perms["deal-blotter"].get("trader") is True
        assert "admin" not in perms["audit-trail"]
        assert "treasury" not in perms["audit-trail"]

    def test_treasury_sees_only_own_role(self, treasury_token):
        r = requests.get(f"{API}/reports/permissions", headers=_h(treasury_token), timeout=15)
        assert r.status_code == 200
        perms = r.json()["permissions"]
        assert perms["audit-trail"].get("treasury") is False
        assert perms["deal-blotter"].get("treasury") is True


# ── PUT /api/reports/permissions ─────────────────────────────
class TestUpdatePermissions:
    def test_trader_forbidden(self, trader_token):
        r = requests.put(f"{API}/reports/permissions", headers=_h(trader_token),
                         json={"permissions": {"deal-blotter": {"trader": False}}}, timeout=15)
        assert r.status_code == 403

    def test_treasury_forbidden(self, treasury_token):
        r = requests.put(f"{API}/reports/permissions", headers=_h(treasury_token),
                         json={"permissions": {"deal-blotter": {"treasury": False}}}, timeout=15)
        assert r.status_code == 403

    def test_admin_toggle_and_verify(self, admin_token, trader_token):
        # Toggle deal-blotter OFF for trader
        r = requests.put(f"{API}/reports/permissions", headers=_h(admin_token),
                         json={"permissions": {"deal-blotter": {"trader": False}}}, timeout=15)
        assert r.status_code == 200
        perms = r.json()["permissions"]
        assert perms["deal-blotter"]["trader"] is False
        assert perms["deal-blotter"]["admin"] is True  # unchanged

        # GET to verify persistence
        g = requests.get(f"{API}/reports/permissions", headers=_h(admin_token), timeout=15)
        assert g.json()["permissions"]["deal-blotter"]["trader"] is False

        # Trader now blocked from deal-blotter
        d = requests.get(f"{API}/reports/deal-blotter?format=json",
                         headers=_h(trader_token), timeout=15)
        assert d.status_code == 403

        # Admin still has access
        da = requests.get(f"{API}/reports/deal-blotter?format=json",
                          headers=_h(admin_token), timeout=15)
        assert da.status_code == 200

        # Re-enable
        r = requests.put(f"{API}/reports/permissions", headers=_h(admin_token),
                         json={"permissions": {"deal-blotter": {"trader": True}}}, timeout=15)
        assert r.status_code == 200
        assert r.json()["permissions"]["deal-blotter"]["trader"] is True

        # Trader restored
        d = requests.get(f"{API}/reports/deal-blotter?format=json",
                         headers=_h(trader_token), timeout=15)
        assert d.status_code == 200

    def test_empty_body_rejected(self, admin_token):
        r = requests.put(f"{API}/reports/permissions", headers=_h(admin_token),
                         json={}, timeout=15)
        assert r.status_code == 400


# ── Default behaviour enforced by _check_report_access ───────
class TestDefaultAccess:
    def test_trader_deal_blotter_allowed(self, trader_token):
        r = requests.get(f"{API}/reports/deal-blotter?format=json",
                         headers=_h(trader_token), timeout=15)
        assert r.status_code == 200

    def test_trader_audit_trail_forbidden(self, trader_token):
        r = requests.get(f"{API}/reports/audit-trail?format=json",
                         headers=_h(trader_token), timeout=15)
        assert r.status_code == 403

    def test_trader_user_activity_forbidden(self, trader_token):
        r = requests.get(f"{API}/reports/user-activity?format=json",
                         headers=_h(trader_token), timeout=15)
        assert r.status_code == 403

    def test_treasury_audit_trail_forbidden(self, treasury_token):
        r = requests.get(f"{API}/reports/audit-trail?format=json",
                         headers=_h(treasury_token), timeout=15)
        assert r.status_code == 403

    def test_admin_audit_trail_allowed(self, admin_token):
        r = requests.get(f"{API}/reports/audit-trail?format=json",
                         headers=_h(admin_token), timeout=15)
        assert r.status_code == 200

    def test_trader_settlement_allowed(self, trader_token):
        r = requests.get(f"{API}/reports/settlement?format=json",
                         headers=_h(trader_token), timeout=15)
        assert r.status_code == 200

    def test_trader_volume_summary_allowed(self, trader_token):
        r = requests.get(f"{API}/reports/volume-summary?format=json",
                         headers=_h(trader_token), timeout=15)
        assert r.status_code == 200

    def test_unauthenticated_permissions_blocked(self):
        r = requests.get(f"{API}/reports/permissions", timeout=15)
        assert r.status_code in (401, 403)
