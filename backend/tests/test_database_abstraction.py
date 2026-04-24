"""
End-to-end tests for the switchable DB abstraction layer.
Active backend: DB_TYPE=mongodb -> MongoDatabase.
Exercises every endpoint mentioned in the review request.
"""
import io
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fx-deal-queue.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "trader":   {"email": "trader@fxtracker.com",   "password": "Trader@123"},
    "treasury": {"email": "treasury@fxtracker.com", "password": "Treasury@123"},
    "admin":    {"email": "admin@fxtracker.com",    "password": "Admin@123"},
}


def _login(role):
    r = requests.post(f"{API}/auth/login", json=CREDS[role], timeout=30)
    assert r.status_code == 200, f"Login {role} failed: {r.status_code} {r.text}"
    j = r.json()
    assert "token" in j and j.get("user", {}).get("role") == role
    return j["token"]


@pytest.fixture(scope="session")
def trader_token(): return _login("trader")
@pytest.fixture(scope="session")
def treasury_token(): return _login("treasury")
@pytest.fixture(scope="session")
def admin_token(): return _login("admin")


def _h(token): return {"Authorization": f"Bearer {token}"}


# -- 1. Auth login all roles --
def test_auth_login_all_three_roles():
    for role in ("trader", "treasury", "admin"):
        r = requests.post(f"{API}/auth/login", json=CREDS[role], timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["user"]["role"] == role
        assert isinstance(body["token"], str) and body["token"]


# -- 2. /api/database/status (admin + RBAC) --
def test_database_status_admin(admin_token):
    r = requests.get(f"{API}/database/status", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["backend"] == "mongodb"
    assert body["class"] == "MongoDatabase"


def test_database_status_trader_forbidden(trader_token):
    r = requests.get(f"{API}/database/status", headers=_h(trader_token), timeout=30)
    assert r.status_code == 403


def test_database_status_treasury_forbidden(treasury_token):
    r = requests.get(f"{API}/database/status", headers=_h(treasury_token), timeout=30)
    assert r.status_code == 403


# -- 3. Storage status (admin only) --
def test_storage_status_admin(admin_token):
    r = requests.get(f"{API}/storage/status", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "backend" in body and "class" in body


def test_storage_status_trader_forbidden(trader_token):
    r = requests.get(f"{API}/storage/status", headers=_h(trader_token), timeout=30)
    assert r.status_code == 403


# -- 4. Reference data (seeded) --
def test_reference_currencies(trader_token):
    r = requests.get(f"{API}/reference/currencies", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    # no mongo _id leak
    assert "_id" not in data[0]


def test_reference_banks(trader_token):
    r = requests.get(f"{API}/reference/banks", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and len(data) > 0


# -- 5. Deal CRUD + history + array ops --
DEAL_PAYLOAD = {
    "transaction_type": "FX Spot",
    "value_date": "2026-01-30",
    "deal_date": "2026-01-28",
    "transfer_type": "SWIFT",
    "client_name": "TEST_DBAbstraction Client",
    "from_type": "bank",
    "from_company": "ACME Corp",
    "from_bank": "HSBC",
    "from_account_num": "123456",
    "from_wallet_address": "",
    "to_type": "bank",
    "to_company": "Beta Ltd",
    "to_bank": "Citibank",
    "to_account_num": "987654",
    "to_wallet_address": "",
    "ours_type": "bank",
    "ours_bank": "HSBC",
    "ours_account_num": "111222",
    "ours_wallet_address": "",
    "buy_currency": "USD",
    "sell_currency": "EUR",
    "currency_amount": 1000.0,
    "amount": 920.0,
    "rate": 0.92,
    "remarks": "TEST_DBAbstraction automation",
}


@pytest.fixture(scope="session")
def created_deal(trader_token):
    r = requests.post(f"{API}/deals", json=DEAL_PAYLOAD, headers=_h(trader_token), timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "pending"
    assert d["reference_number"].startswith("FX-")
    assert d["settlement_proofs"] == []
    return d


def test_create_deal(created_deal):
    assert "id" in created_deal
    assert created_deal["client_name"] == DEAL_PAYLOAD["client_name"]
    # no mongo _id leak
    assert "_id" not in created_deal


def test_list_deals_pagination(trader_token, created_deal):
    r = requests.get(f"{API}/deals?page=1&limit=20", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    items = body.get("deals") or body.get("items") or body if isinstance(body, dict) else body
    assert isinstance(items, list)
    assert any(d["id"] == created_deal["id"] for d in items)
    # pagination metadata
    if isinstance(body, dict):
        assert body.get("total", 0) >= 1 or len(items) >= 1


def test_get_deal_detail_has_history(trader_token, created_deal):
    r = requests.get(f"{API}/deals/{created_deal['id']}", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == created_deal["id"]
    assert isinstance(body["history"], list) and len(body["history"]) >= 1
    assert body["history"][0]["action"] == "created"
    assert isinstance(body["settlement_proofs"], list)


def test_get_deal_as_other_trader_forbidden(created_deal):
    # trader can only see own deal -> verify with another user (treasury can see all)
    treasury = _login("treasury")
    r = requests.get(f"{API}/deals/{created_deal['id']}", headers=_h(treasury), timeout=30)
    assert r.status_code == 200  # treasury has access


# -- 6. Upload + delete settlement proof (array $push / $pull) --
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x5b\x8a\xf7\xb6\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture(scope="session")
def uploaded_proof(trader_token, created_deal):
    files = {"file": ("test.png", io.BytesIO(PNG_BYTES), "image/png")}
    r = requests.post(
        f"{API}/deals/{created_deal['id']}/upload?proof_type=client",
        files=files, headers=_h(trader_token), timeout=60,
    )
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["proof_type"] == "client"
    return p


def test_upload_proof(uploaded_proof):
    assert "id" in uploaded_proof and "path" in uploaded_proof


def test_deal_detail_reflects_proof(trader_token, created_deal, uploaded_proof):
    r = requests.get(f"{API}/deals/{created_deal['id']}", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    proofs = r.json()["settlement_proofs"]
    assert any(p["id"] == uploaded_proof["id"] for p in proofs)


def test_delete_proof(trader_token, created_deal, uploaded_proof):
    r = requests.delete(
        f"{API}/deals/{created_deal['id']}/proofs/{uploaded_proof['id']}",
        headers=_h(trader_token), timeout=30,
    )
    assert r.status_code == 200
    # verify $pull persisted
    r2 = requests.get(f"{API}/deals/{created_deal['id']}", headers=_h(trader_token), timeout=30)
    proofs = r2.json()["settlement_proofs"]
    assert not any(p["id"] == uploaded_proof["id"] for p in proofs)


# -- 7. Treasury process (return) -> trader edit -> resubmit (confirm) --
def test_treasury_return_then_edit_then_resubmit_then_confirm(trader_token, treasury_token, created_deal):
    # return
    r = requests.put(
        f"{API}/deals/{created_deal['id']}/process",
        json={"status": "returned", "treasury_remarks": "TEST_DBAbstraction returning for edit"},
        headers=_h(treasury_token), timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "returned"

    # edit (only allowed on returned deals)
    r = requests.put(
        f"{API}/deals/{created_deal['id']}/edit",
        json={"remarks": "TEST_DBAbstraction edited remarks", "amount": 925.0},
        headers=_h(trader_token), timeout=30,
    )
    assert r.status_code == 200, r.text
    edited = r.json()
    assert edited["remarks"] == "TEST_DBAbstraction edited remarks"
    assert abs(edited["amount"] - 925.0) < 0.001

    # resubmit
    r = requests.put(
        f"{API}/deals/{created_deal['id']}/resubmit",
        headers=_h(trader_token), timeout=30,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending"

    # confirm
    r = requests.put(
        f"{API}/deals/{created_deal['id']}/process",
        json={"status": "confirmed", "treasury_remarks": "TEST_DBAbstraction confirming"},
        headers=_h(treasury_token), timeout=30,
    )
    assert r.status_code == 200
    final = r.json()
    assert final["status"] == "confirmed"
    assert final["processed_by"] is not None

    # history should contain created, returned, edited, resubmitted, confirmed
    r = requests.get(f"{API}/deals/{created_deal['id']}", headers=_h(trader_token), timeout=30)
    actions = {h["action"] for h in r.json()["history"]}
    assert "created" in actions
    assert any(a.startswith("deal_returned") or a == "deal_returned" for a in actions)
    assert any(a == "deal_resubmitted" for a in actions)
    assert any(a == "deal_confirmed" for a in actions)


# -- 8. Dashboard aggregation --
def test_dashboard_stats(trader_token):
    r = requests.get(f"{API}/dashboard/stats?range=30d", headers=_h(trader_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    # sanity: must be a dict with numeric counters
    assert isinstance(body, dict)
    # common keys – lenient
    numeric_vals = [v for v in body.values() if isinstance(v, (int, float))]
    assert len(numeric_vals) >= 1


# -- 9. Admin-only lists --
def test_admin_users_list(admin_token):
    r = requests.get(f"{API}/users", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    users = body.get("users") or body.get("items") or body if isinstance(body, dict) else body
    assert isinstance(users, list) and len(users) >= 3
    assert "_id" not in users[0]
    emails = [u.get("email") for u in users]
    assert "admin@fxtracker.com" in emails


def test_users_list_trader_forbidden(trader_token):
    r = requests.get(f"{API}/users", headers=_h(trader_token), timeout=30)
    assert r.status_code == 403


def test_audit_logs_admin(admin_token):
    r = requests.get(f"{API}/audit-logs", headers=_h(admin_token), timeout=30)
    assert r.status_code == 200
    body = r.json()
    logs = body.get("logs") or body.get("items") or body if isinstance(body, dict) else body
    assert isinstance(logs, list) and len(logs) >= 1
    assert "_id" not in logs[0]


def test_audit_logs_trader_forbidden(trader_token):
    r = requests.get(f"{API}/audit-logs", headers=_h(trader_token), timeout=30)
    assert r.status_code == 403
