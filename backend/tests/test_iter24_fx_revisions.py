"""
Iteration 24 — FX Trading Tracker revision tests
Covers backend pieces from the 9-item revision:
- Item 6: GET /api/reference/transfer-types must include 'FX Bank Deal'
- Item 6: POST /api/deals can create with transfer_type='FX Bank Deal' and empty Destination fields
- PHP-divide acceptance: POST /api/deals with Buy=PHP, Sell=USD, amount=50000, rate=56
- Item 2: GET /api/deals returns 'history' on list items so FE can show Last Action
"""
import os
import pytest
import requests
from datetime import datetime, timezone

def _load_backend_url():
    import re
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    m = re.match(r"^REACT_APP_BACKEND_URL\s*=\s*(.+)$", line.strip())
                    if m:
                        url = m.group(1).strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    assert url, "REACT_APP_BACKEND_URL not set"
    return url.rstrip("/")

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def trader_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": "trader@fxtracker.com", "password": "Trader@123"
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def trader_headers(trader_token):
    return {"Authorization": f"Bearer {trader_token}", "Content-Type": "application/json"}


# ---------- Item 6: transfer types reference ----------
class TestTransferTypesReference:
    def test_fx_bank_deal_present(self, trader_headers):
        r = requests.get(f"{API}/reference/transfer-types", headers=trader_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        names = [t.get("name") for t in data]
        assert "FX Bank Deal" in names, f"Missing FX Bank Deal in transfer types: {names}"
        # The other expected types are still there
        for expected in ("FX Crypto Conversion", "FX Local", "PDAX Withdrawal"):
            assert expected in names, f"Missing {expected} in transfer types: {names}"

    def test_fx_bank_deal_active(self, trader_headers):
        r = requests.get(f"{API}/reference/transfer-types", headers=trader_headers, timeout=20)
        assert r.status_code == 200
        rec = next((t for t in r.json() if t.get("name") == "FX Bank Deal"), None)
        assert rec is not None
        assert rec.get("is_active") in (True, "true", 1)


# ---------- Item 6: create deal with FX Bank Deal + empty destination ----------
def _deal_payload(transfer_type, amount=50000, rate=56, buy="PHP", sell="USD",
                  has_destination=True):
    payload = {
        "client_name": "TEST_Acme Corporation",
        "transaction_type": "Spot",
        "transfer_type": transfer_type,
        "deal_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "value_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "buy_currency": buy,
        "sell_currency": sell,
        "currency_amount": amount,
        "rate": rate,
        "amount": (amount / rate) if buy == "PHP" else (amount * rate),
        "from_type": "bank",
        "from_company": "GlobalTech Inc",
        "from_bank": "BDO",
        "from_account_num": "1234567890",
        "ours_type": "bank",
        "ours_bank": "BDO",
        "ours_account_num": "9999999999",
        "remarks": "TEST_iter24",
    }
    if has_destination:
        payload.update({
            "to_type": "bank",
            "to_company": "Acme Corporation",
            "to_bank": "Metrobank",
            "to_account_num": "0987654321",
        })
    else:
        # FX Bank Deal: destination omitted/blank
        payload.update({
            "to_type": "",
            "to_company": "",
            "to_bank": "",
            "to_account_num": "",
        })
    return payload


class TestFxBankDealCreate:
    created_id = None

    def test_create_fx_bank_deal_empty_destination(self, trader_headers):
        payload = _deal_payload("FX Bank Deal", has_destination=False)
        r = requests.post(f"{API}/deals", headers=trader_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), f"FX Bank Deal create failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("transfer_type") == "FX Bank Deal"
        assert body.get("to_company", "") in ("", None)
        TestFxBankDealCreate.created_id = body.get("id")
        assert TestFxBankDealCreate.created_id

    def test_created_deal_is_fetchable(self, trader_headers):
        assert TestFxBankDealCreate.created_id, "previous test failed"
        r = requests.get(f"{API}/deals/{TestFxBankDealCreate.created_id}", headers=trader_headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        assert body.get("transfer_type") == "FX Bank Deal"
        # destination should be empty/blank, not required
        assert (body.get("to_company") or "") == ""
        assert (body.get("to_bank") or "") == ""


# ---------- PHP divide acceptance ----------
class TestPhpDivideDeal:
    def test_php_buy_usd_sell_divides(self, trader_headers):
        payload = _deal_payload("FX Crypto Conversion", amount=50000, rate=56,
                                buy="PHP", sell="USD", has_destination=True)
        # Frontend computes amount = 50000/56 = 892.857...
        r = requests.post(f"{API}/deals", headers=trader_headers, json=payload, timeout=30)
        assert r.status_code in (200, 201), f"PHP divide deal failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("buy_currency") == "PHP"
        assert body.get("sell_currency") == "USD"
        # Backend must accept the divided amount without rejecting
        assert float(body.get("amount", 0)) == pytest.approx(50000 / 56, rel=1e-3)


# ---------- Item 2: list deals returns history ----------
class TestDealsListHistory:
    def test_history_in_list_response(self, trader_headers):
        r = requests.get(f"{API}/deals?limit=10", headers=trader_headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        rows = body.get("deals") or body.get("rows") if isinstance(body, dict) else body
        assert rows, "no deals returned"
        # At least one row should have history populated (deals always log on create)
        any_history = any(isinstance(d.get("history"), list) and len(d.get("history")) > 0 for d in rows)
        assert any_history, "No row exposes history[] - Last Action column cannot render"

    def test_history_entries_shape(self, trader_headers):
        r = requests.get(f"{API}/deals?limit=10", headers=trader_headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        rows = body.get("deals") or body.get("rows") if isinstance(body, dict) else body
        for d in rows:
            h = d.get("history") or []
            for entry in h:
                # action/event name expected
                assert any(k in entry for k in ("action", "event", "type", "status")), entry
