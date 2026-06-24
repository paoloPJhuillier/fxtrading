"""
Iteration 26 - FX Trading Tracker feedback items 0-9 backend regression
Tests:
  Item 0: GET /api/reference/transaction-types returns Buy / Sell only
  Item 1: GET/POST /api/reference/counterparties (seed CLSC/PJ/Verite + admin create)
  Item 4: GET /api/reference/transfer-types includes FX-Intercompany
  Item 6: POST /api/deals with transfer_type=FX-Intercompany persists buying_ours_*
  Item 7: GET /api/reports/settlement?format=json -> .1 & .2 rows for Interco
  Item 8: GET /api/reports/tms?format=json TMS columns + dual lines + CSV SAP headers
"""
import os
import io
import csv
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

TRADER = {"email": "trader@fxtracker.com", "password": "Trader@123"}
ADMIN = {"email": "admin@fxtracker.com", "password": "Admin@123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed {creds['email']}: {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def trader_token():
    return _login(TRADER)


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def trader_h(trader_token):
    return {"Authorization": f"Bearer {trader_token}"}


@pytest.fixture(scope="module")
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ----------- Item 0 : transaction types Buy/Sell -----------
def test_item0_transaction_types_buy_sell(trader_h):
    r = requests.get(f"{API}/reference/transaction-types", headers=trader_h, timeout=20)
    assert r.status_code == 200, r.text
    names = sorted([x.get("name") for x in r.json()])
    assert names == ["Buy", "Sell"], f"Expected Buy/Sell, got {names}"
    # Negative: old types absent
    for old in ["Today", "Tomorrow", "Spot"]:
        assert old not in names


# ----------- Item 1 : counterparties CRUD -----------
def test_item1_counterparties_seed(trader_h):
    r = requests.get(f"{API}/reference/counterparties", headers=trader_h, timeout=20)
    assert r.status_code == 200, r.text
    codes = sorted([x.get("code") for x in r.json()])
    for expected in ["CLSC", "PJ", "Verite"]:
        assert expected in codes, f"Missing counterparty {expected}; got {codes}"


def test_item1_counterparty_create_admin(admin_h, trader_h):
    payload = {"name": f"TEST_CP_{uuid.uuid4().hex[:6]}", "code": f"TST{uuid.uuid4().hex[:4].upper()}"}
    r = requests.post(f"{API}/reference/counterparties", json=payload, headers=admin_h, timeout=20)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["name"] == payload["name"]
    assert created["code"] == payload["code"]
    cid = created["id"]
    # verify via GET
    r2 = requests.get(f"{API}/reference/counterparties", headers=trader_h, timeout=20)
    found = [c for c in r2.json() if c["id"] == cid]
    assert found, "Created counterparty not returned in GET list"
    # cleanup
    requests.delete(f"{API}/reference/counterparties/{cid}", headers=admin_h, timeout=20)


def test_item1_counterparty_create_trader_forbidden(trader_h):
    payload = {"name": "TEST_NOAUTH", "code": "NOAUTH"}
    r = requests.post(f"{API}/reference/counterparties", json=payload, headers=trader_h, timeout=20)
    assert r.status_code == 403, f"Expected 403 trader create, got {r.status_code}"


# ----------- Item 4 : transfer-types includes FX-Intercompany -----------
def test_item4_transfer_types_has_intercompany(trader_h):
    r = requests.get(f"{API}/reference/transfer-types", headers=trader_h, timeout=20)
    assert r.status_code == 200, r.text
    names = [x.get("name") for x in r.json()]
    assert "FX-Intercompany" in names, f"FX-Intercompany missing: {names}"


# ----------- helper: pick refs to build a deal -----------
def _ref_first(token, ep):
    r = requests.get(f"{API}/reference/{ep}", headers={"Authorization": f"Bearer {token}"}, timeout=20)
    return r.json()


@pytest.fixture(scope="module")
def interco_deal_id(trader_token):
    h = {"Authorization": f"Bearer {trader_token}"}
    cp = _ref_first(trader_token, "counterparties")
    currencies = _ref_first(trader_token, "currencies")
    banks = _ref_first(trader_token, "banks")
    assert cp and currencies and banks, "missing reference seeds"
    fiat = next((c for c in currencies if c.get("type", "fiat") == "fiat"), currencies[0])
    other = next((c for c in currencies if c["code"] != fiat["code"]), currencies[-1])
    payload = {
        "client_name": "TEST_INTERCO_CLIENT",
        "counterparty": cp[0]["name"],
        "transaction_type": "Buy",
        "transfer_type": "FX-Intercompany",
        "buy_currency": fiat["code"],
        "sell_currency": other["code"],
        "currency_amount": 100000,
        "rate": 56.5,
        "amount": 5650000,
        "deal_date": "2026-01-15",
        "value_date": "2026-01-17",
        "from_type": "bank",
        "from_company": cp[0]["name"],
        "from_bank": banks[0]["name"],
        "from_account_num": "1234567890",
        "to_type": "bank",
        "to_company": cp[0]["name"],
        "to_bank": banks[0]["name"],
        "to_account_num": "0987654321",
        "ours_type": "bank",
        "ours_bank": banks[0]["name"],
        "ours_account_num": "1111111111",
        "buying_ours_type": "bank",
        "buying_ours_bank": banks[0]["name"],
        "buying_ours_account_num": "2222222222",
        "remarks": "TEST_INTERCO",
    }
    r = requests.post(f"{API}/deals", json=payload, headers=h, timeout=30)
    assert r.status_code in (200, 201), f"deal create failed: {r.status_code} {r.text}"
    deal = r.json()
    return deal["id"]


# ----------- Item 6 : Interco deal persists buying_ours_* -----------
def test_item6_interco_deal_buying_ours_persisted(trader_h, interco_deal_id):
    r = requests.get(f"{API}/deals/{interco_deal_id}", headers=trader_h, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["transfer_type"] == "FX-Intercompany"
    assert d.get("buying_ours_bank"), "buying_ours_bank empty"
    assert d.get("buying_ours_account_num") == "2222222222"
    assert d.get("ours_account_num") == "1111111111"  # selling ours separate


# ----------- Item 7 : settlement report dual lines -----------
def test_item7_settlement_dual_lines(trader_h, interco_deal_id):
    # interco deals are pending by default (status filter accepts pending+confirmed)
    r = requests.get(f"{API}/reports/settlement?format=json&limit=500", headers=trader_h, timeout=30)
    assert r.status_code == 200, r.text
    rows = r.json().get("rows", [])
    # locate our deal by reference -> need it from get
    deal = requests.get(f"{API}/deals/{interco_deal_id}", headers=trader_h, timeout=20).json()
    ref = deal["reference_number"]
    matched = [r for r in rows if r["reference_number"].startswith(ref)]
    refs = sorted([r["reference_number"] for r in matched])
    assert f"{ref}.1" in refs and f"{ref}.2" in refs, f"Expected dual lines for {ref}, got {refs}"
    txn_types = {r["reference_number"]: r["transaction_type"] for r in matched}
    assert txn_types[f"{ref}.1"] == "Sell"
    assert txn_types[f"{ref}.2"] == "Buy"


# ----------- Item 8 : TMS Report -----------
TMS_KEYS = {"buy_or_trade", "type_of_transfer", "from_co", "to_co", "fx_partner",
            "maker", "approver", "buy_curr", "sell_curr", "ref_no", "rate", "status"}


def test_item8_tms_json_columns(trader_h, interco_deal_id):
    r = requests.get(f"{API}/reports/tms?format=json&limit=500", headers=trader_h, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    rows = j.get("rows", [])
    assert rows, "TMS rows empty"
    sample = rows[0]
    missing = TMS_KEYS - set(sample.keys())
    assert not missing, f"TMS JSON missing keys: {missing}"


def test_item8_tms_interco_dual_lines(trader_h, interco_deal_id):
    r = requests.get(f"{API}/reports/tms?format=json&limit=500", headers=trader_h, timeout=30)
    rows = r.json()["rows"]
    deal = requests.get(f"{API}/deals/{interco_deal_id}", headers=trader_h, timeout=20).json()
    ref = deal["reference_number"]
    ours = [r for r in rows if r["ref_no"].startswith(ref)]
    txn = {r["ref_no"]: r["buy_or_trade"] for r in ours}
    assert txn.get(f"{ref}.1") == "Sell"
    assert txn.get(f"{ref}.2") == "Buy"


def test_item8_tms_csv_sap_headers(trader_h):
    r = requests.get(f"{API}/reports/tms?format=csv", headers=trader_h, timeout=30)
    assert r.status_code == 200, r.text
    assert "text/csv" in r.headers.get("content-type", "")
    reader = csv.reader(io.StringIO(r.text))
    header = next(reader)
    expected = ["Buy or Trade", "Type of Transfer", "From Co", "From Bank", "From Acct No",
                "To Co", "To Bank", "To Acct No", "Buy Curr", "Sell Curr",
                "Buy FX Amt", "Sell FX Amt", "Ref. No", "FX Partner", "Rate",
                "Status", "Remarks", "Maker", "Date Submitted", "Approver", "Date Authorized"]
    assert header == expected, f"CSV headers mismatch: {header}"


# ----------- cleanup interco deal at end (best-effort) -----------
def test_zz_cleanup_interco(admin_h, interco_deal_id):
    # admins may not delete deals via standard route; just ensure GET still works (no-op cleanup)
    r = requests.get(f"{API}/deals/{interco_deal_id}", headers=admin_h, timeout=20)
    assert r.status_code in (200, 404)
