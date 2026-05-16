"""System Administration (sysadmin role) tests - iteration 25."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fx-deal-queue.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SYS = ("sysadmin@fxtracker.com", "SysAdmin@123")
ADMIN = ("admin@fxtracker.com", "Admin@123")
TRADER = ("trader@fxtracker.com", "Trader@123")


def _login(email, pw):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw}, timeout=15)
    return r


def _token(email, pw):
    r = _login(email, pw)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def sys_token():
    return _token(*SYS)


@pytest.fixture(scope="module")
def admin_token():
    return _token(*ADMIN)


@pytest.fixture(scope="module")
def trader_token():
    return _token(*TRADER)


# ---------- Auth & role inheritance ----------
class TestAuth:
    def test_sysadmin_login_role(self):
        r = _login(*SYS)
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["user"]["role"] == "sysadmin"
        assert data["user"]["email"] == SYS[0]


# ---------- /api/system/db-stats ----------
class TestDbStats:
    def test_stats_as_sysadmin(self, sys_token):
        r = requests.get(f"{API}/system/db-stats", headers={"Authorization": f"Bearer {sys_token}"}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "stats" in data
        for k in ["deals", "audit_logs", "users", "companies", "banks", "bank_accounts",
                  "currencies", "transaction_types", "transfer_types"]:
            assert k in data["stats"], f"missing key {k}"
            assert isinstance(data["stats"][k], int)

    def test_stats_as_admin_forbidden(self, admin_token):
        r = requests.get(f"{API}/system/db-stats", headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code == 403

    def test_stats_as_trader_forbidden(self, trader_token):
        r = requests.get(f"{API}/system/db-stats", headers={"Authorization": f"Bearer {trader_token}"}, timeout=15)
        assert r.status_code == 403


# ---------- /api/system/export/{entity} ----------
class TestExport:
    def test_export_deals_csv(self, sys_token):
        r = requests.get(f"{API}/system/export/deals", params={"format": "csv"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        assert "attachment" in r.headers.get("content-disposition", "")

    def test_export_deals_json(self, sys_token):
        r = requests.get(f"{API}/system/export/deals", params={"format": "json"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_export_banks_json(self, sys_token):
        r = requests.get(f"{API}/system/export/banks", params={"format": "json"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_export_bank_accounts_csv(self, sys_token):
        r = requests.get(f"{API}/system/export/bank_accounts", params={"format": "csv"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")

    def test_export_users_csv_excludes_password(self, sys_token):
        r = requests.get(f"{API}/system/export/users", params={"format": "csv"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200
        body = r.text
        header_line = body.split("\n", 1)[0]
        assert "password_hash" not in header_line, f"password_hash leaked in CSV header: {header_line}"

    def test_export_invalid_entity(self, sys_token):
        r = requests.get(f"{API}/system/export/invalid_entity",
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=15)
        assert r.status_code == 400

    def test_export_as_admin_forbidden(self, admin_token):
        r = requests.get(f"{API}/system/export/deals", params={"format": "json"},
                         headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code == 403


# ---------- /api/system/db-reset ----------
class TestDbReset:
    def test_reset_wrong_confirm(self, sys_token):
        r = requests.post(f"{API}/system/db-reset", json={"confirm": "wrong"},
                          headers={"Authorization": f"Bearer {sys_token}"}, timeout=15)
        assert r.status_code == 400

    def test_reset_as_admin_forbidden(self, admin_token):
        r = requests.post(f"{API}/system/db-reset", json={"confirm": "RESET DATABASE"},
                          headers={"Authorization": f"Bearer {admin_token}"}, timeout=15)
        assert r.status_code == 403

    def test_reset_as_trader_forbidden(self, trader_token):
        r = requests.post(f"{API}/system/db-reset", json={"confirm": "RESET DATABASE"},
                          headers={"Authorization": f"Bearer {trader_token}"}, timeout=15)
        assert r.status_code == 403


# ---------- sysadmin inherits admin permissions ----------
class TestSysadminInheritsAdmin:
    def test_sysadmin_can_list_users(self, sys_token):
        r = requests.get(f"{API}/users", headers={"Authorization": f"Bearer {sys_token}"}, timeout=15)
        assert r.status_code == 200

    def test_sysadmin_can_view_audit_logs(self, sys_token):
        r = requests.get(f"{API}/audit-logs", headers={"Authorization": f"Bearer {sys_token}"}, timeout=15)
        assert r.status_code == 200

    def test_sysadmin_can_access_reports(self, sys_token):
        r = requests.get(f"{API}/reports/deal-blotter", params={"format": "json"},
                         headers={"Authorization": f"Bearer {sys_token}"}, timeout=30)
        assert r.status_code == 200


# ---------- DB Reset functional flow (run LAST) ----------
class TestDbResetFunctional:
    """Performs actual DB reset and validates wipe + retention."""

    def test_z_actual_reset_wipes_deals_retains_users(self, sys_token, admin_token):
        h_sys = {"Authorization": f"Bearer {sys_token}"}
        # Get pre-stats
        pre = requests.get(f"{API}/system/db-stats", headers=h_sys, timeout=15).json()["stats"]
        users_before = pre["users"]
        companies_before = pre["companies"]
        currencies_before = pre["currencies"]

        # Perform reset
        r = requests.post(f"{API}/system/db-reset", json={"confirm": "RESET DATABASE"},
                          headers=h_sys, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["wiped"]["deals"] == pre["deals"]
        assert "users" in body["retained"]

        # Get post-stats
        post = requests.get(f"{API}/system/db-stats", headers=h_sys, timeout=15).json()["stats"]
        assert post["deals"] == 0, "deals should be 0 after reset"
        assert post["audit_logs"] == 0, "audit_logs should be 0 after reset"
        assert post["counters"] == 0
        assert post["users"] == users_before, "users must be retained"
        assert post["companies"] == companies_before
        assert post["currencies"] == currencies_before
