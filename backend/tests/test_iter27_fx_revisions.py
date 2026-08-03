"""Iteration 27 - FX Tracker 12 feedback items backend tests."""
import os
import io
import csv
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

ADMIN = {"email": "admin@fxtracker.com", "password": "Admin@123"}
TRADER = {"email": "trader@fxtracker.com", "password": "Trader@123"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def trader_token():
    return _login(TRADER)


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def trader_headers(trader_token):
    return {"Authorization": f"Bearer {trader_token}"}


# --- Item 3: USDC display name changed to "USD Circle" ---
def test_usdc_named_usd_circle(admin_headers):
    r = requests.get(f"{BASE_URL}/api/reference/currencies", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    ccys = r.json()
    usdc = next((c for c in ccys if c["code"] == "USDC"), None)
    assert usdc is not None, "USDC currency not found"
    assert usdc["name"] == "USD Circle", f"Expected 'USD Circle', got '{usdc.get('name')}'"


# --- Item 11: FX - Corporate Settlement transfer type present ---
def test_transfer_type_corporate_settlement(admin_headers):
    r = requests.get(f"{BASE_URL}/api/reference/transfer-types", headers=admin_headers, timeout=20)
    assert r.status_code == 200
    names = [t["name"] for t in r.json()]
    assert "FX - Corporate Settlement" in names, f"Missing FX - Corporate Settlement in {names}"
    assert "FX Local" in names
    assert "FX-Intercompany" in names


# --- Item 7: Bank account creation requires account_name ---
def test_bank_account_requires_account_name(admin_headers):
    banks = requests.get(f"{BASE_URL}/api/reference/banks", headers=admin_headers, timeout=20).json()
    assert len(banks) > 0
    bank_id = banks[0]["id"]

    # Missing account_name -> should fail (Pydantic 422 or 400)
    r = requests.post(
        f"{BASE_URL}/api/reference/banks/{bank_id}/accounts",
        json={"account_number": f"TEST{uuid.uuid4().hex[:6]}"},
        headers=admin_headers, timeout=20
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text}"

    # Empty string account_name -> should also fail
    r = requests.post(
        f"{BASE_URL}/api/reference/banks/{bank_id}/accounts",
        json={"account_number": f"TEST{uuid.uuid4().hex[:6]}", "account_name": "   "},
        headers=admin_headers, timeout=20
    )
    assert r.status_code == 400, f"Expected 400 for blank name, got {r.status_code}: {r.text}"

    # Valid creation
    acct_num = f"TEST{uuid.uuid4().hex[:8]}"
    r = requests.post(
        f"{BASE_URL}/api/reference/banks/{bank_id}/accounts",
        json={"account_number": acct_num, "account_name": "TEST_Account_Name"},
        headers=admin_headers, timeout=20
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["account_name"] == "TEST_Account_Name"
    assert data["account_number"] == acct_num

    # Cleanup
    acct_id = data["id"]
    requests.delete(f"{BASE_URL}/api/reference/banks/{bank_id}/accounts/{acct_id}", headers=admin_headers, timeout=20)


# --- Item 9: Bank accounts CSV import ---
def test_bank_accounts_csv_import(admin_headers):
    banks = requests.get(f"{BASE_URL}/api/reference/banks", headers=admin_headers, timeout=20).json()
    bank_id = banks[0]["id"]

    csv_content = "account_number,account_name\n"
    a1 = f"TESTIMP{uuid.uuid4().hex[:6]}"
    a2 = f"TESTIMP{uuid.uuid4().hex[:6]}"
    csv_content += f"{a1},TEST_Import_A\n{a2},TEST_Import_B\n"

    files = {"file": ("accounts.csv", csv_content, "text/csv")}
    r = requests.post(
        f"{BASE_URL}/api/reference/banks/{bank_id}/accounts/import",
        files=files, headers=admin_headers, timeout=30
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["created"] >= 2, f"Expected at least 2 created, got {data}"

    # Verify they exist via GET
    accts = requests.get(f"{BASE_URL}/api/reference/banks/{bank_id}/accounts", headers=admin_headers, timeout=20).json()
    nums = [a["account_number"] for a in accts]
    assert a1 in nums and a2 in nums

    # Cleanup
    for a in accts:
        if a["account_number"] in (a1, a2):
            requests.delete(f"{BASE_URL}/api/reference/banks/{bank_id}/accounts/{a['id']}", headers=admin_headers, timeout=20)


def test_bank_accounts_import_requires_admin(trader_headers):
    banks_r = requests.get(f"{BASE_URL}/api/reference/banks", headers=trader_headers, timeout=20)
    if banks_r.status_code != 200:
        pytest.skip("Trader cannot list banks")
    banks = banks_r.json()
    if not banks:
        pytest.skip("No banks")
    bank_id = banks[0]["id"]
    files = {"file": ("x.csv", "account_number,account_name\nX,Y\n", "text/csv")}
    r = requests.post(f"{BASE_URL}/api/reference/banks/{bank_id}/accounts/import", files=files, headers=trader_headers, timeout=20)
    assert r.status_code == 403


# --- Item 10: FX Client (companies) CSV import ---
def test_companies_csv_import(admin_headers):
    csv_content = "name,code,type\n"
    c1 = f"TCOMP{uuid.uuid4().hex[:6].upper()}"
    c2 = f"TCOMP{uuid.uuid4().hex[:6].upper()}"
    csv_content += f"TEST Company A,{c1},Customer\nTEST Company B,{c2},Vendor\n"

    files = {"file": ("companies.csv", csv_content, "text/csv")}
    r = requests.post(f"{BASE_URL}/api/reference/companies/import", files=files, headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["created"] >= 2, data

    # Verify persisted
    comps = requests.get(f"{BASE_URL}/api/reference/companies", headers=admin_headers, timeout=20).json()
    codes = [c["code"] for c in comps]
    assert c1 in codes and c2 in codes

    # Cleanup - find id and delete
    for c in comps:
        if c["code"] in (c1, c2):
            requests.delete(f"{BASE_URL}/api/reference/companies/{c['id']}", headers=admin_headers, timeout=20)


def test_companies_import_requires_admin(trader_headers):
    files = {"file": ("x.csv", "name,code\nA,B\n", "text/csv")}
    r = requests.post(f"{BASE_URL}/api/reference/companies/import", files=files, headers=trader_headers, timeout=20)
    assert r.status_code == 403


# --- Item 11: Deal creation with FX - Corporate Settlement ---
def test_deal_creation_fx_corporate_settlement(trader_headers):
    payload = {
        "client_name": "TEST_CORP_SETTLE",
        "counterparty": "CLSC",
        "transaction_type": "Buy",
        "transfer_type": "FX - Corporate Settlement",
        "buy_currency": "USD",
        "sell_currency": "PHP",
        "currency_amount": 1000,
        "amount": 56500,
        "rate": 56.5,
        "deal_date": "2026-01-15",
        "value_date": "2026-01-15",
        "from_type": "bank",
        "from_company": "TEST_CORP_SETTLE",
        "from_bank": "BDO",
        "from_account_num": "1234567890",
        "to_type": "bank",
        "to_bank": "BDO",
        "to_account_num": "0987654321",
        "ours_type": "bank",
        "ours_bank": "BDO",
        "ours_account_num": "1111111111",
    }
    r = requests.post(f"{BASE_URL}/api/deals", json=payload, headers=trader_headers, timeout=30)
    assert r.status_code == 200, r.text
    deal = r.json()
    assert deal["transfer_type"] == "FX - Corporate Settlement"
    assert deal["counterparty"] == "CLSC"


# --- Item 12/14: Deal creation with crypto network fields ---
def test_deal_creation_crypto_network(trader_headers):
    payload = {
        "client_name": "TEST_CRYPTO_NET",
        "transaction_type": "Buy",
        "transfer_type": "FX Crypto Conversion",
        "buy_currency": "USDT",
        "sell_currency": "PHP",
        "currency_amount": 500,
        "amount": 28250,
        "rate": 56.5,
        "deal_date": "2026-01-15",
        "value_date": "2026-01-15",
        "from_type": "crypto",
        "from_company": "TEST_CRYPTO_NET",
        "from_wallet_address": "0xTESTWALLETFROM",
        "from_network": "ETHEREUM",
        "to_type": "crypto",
        "to_wallet_address": "0xTESTWALLETTO",
        "to_network": "SOLANA",
        "ours_type": "crypto",
        "ours_wallet_address": "0xTESTOURSADDR",
        "ours_network": "TRON",
    }
    r = requests.post(f"{BASE_URL}/api/deals", json=payload, headers=trader_headers, timeout=30)
    assert r.status_code == 200, r.text
    deal = r.json()
    deal_id = deal["id"]

    # GET to verify persistence
    r = requests.get(f"{BASE_URL}/api/deals/{deal_id}", headers=trader_headers, timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["from_network"] == "ETHEREUM"
    assert d["to_network"] == "SOLANA"
    assert d["ours_network"] == "TRON"
    assert d["from_type"] == "crypto"
