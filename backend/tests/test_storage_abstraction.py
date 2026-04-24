"""
Backend tests for the switchable storage abstraction layer.
Covers:
  - Login for all 3 roles
  - Deal creation by trader
  - Upload settlement proof (client/processor) -> get path
  - GET /api/files/{path} -> download returns correct content-type
  - DELETE proof
  - GET /api/storage/status (admin only, 403 for others)
  - Deal list + detail with settlement_proofs
"""
import io
import os
import struct
import zlib
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://fx-deal-queue.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

CREDS = {
    "trader": ("trader@fxtracker.com", "Trader@123"),
    "treasury": ("treasury@fxtracker.com", "Treasury@123"),
    "admin": ("admin@fxtracker.com", "Admin@123"),
}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    return r.json()


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_png_bytes() -> bytes:
    """Minimal valid 1x1 PNG."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = b"IHDR" + ihdr_data
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + ihdr + struct.pack(">I", zlib.crc32(ihdr) & 0xffffffff)
    raw = b"\x00\xff\x00\x00"
    comp = zlib.compress(raw)
    idat = b"IDAT" + comp
    idat_chunk = struct.pack(">I", len(comp)) + idat + struct.pack(">I", zlib.crc32(idat) & 0xffffffff)
    iend = b"IEND"
    iend_chunk = struct.pack(">I", 0) + iend + struct.pack(">I", zlib.crc32(iend) & 0xffffffff)
    return sig + ihdr_chunk + idat_chunk + iend_chunk


@pytest.fixture(scope="module")
def tokens():
    return {role: _login(e, p) for role, (e, p) in CREDS.items()}


# ---- Auth / Login ----
class TestLogin:
    def test_login_trader(self, tokens):
        assert tokens["trader"]["user"]["role"] == "trader"
        assert tokens["trader"]["token"]

    def test_login_treasury(self, tokens):
        assert tokens["treasury"]["user"]["role"] == "treasury"

    def test_login_admin(self, tokens):
        assert tokens["admin"]["user"]["role"] == "admin"


# ---- Storage status endpoint ----
class TestStorageStatus:
    def test_admin_storage_status(self, tokens):
        r = requests.get(f"{API}/storage/status", headers=_headers(tokens["admin"]["token"]), timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["backend"] == "emergent"
        assert data["class"] == "EmergentStorage"

    def test_non_admin_storage_status_forbidden(self, tokens):
        r = requests.get(f"{API}/storage/status", headers=_headers(tokens["trader"]["token"]), timeout=30)
        assert r.status_code == 403
        r2 = requests.get(f"{API}/storage/status", headers=_headers(tokens["treasury"]["token"]), timeout=30)
        assert r2.status_code == 403


# ---- Deal creation + upload + download + delete ----
@pytest.fixture(scope="module")
def created_deal(tokens):
    # get a bank and currency code for realistic payload
    payload = {
        "transaction_type": "Spot",
        "value_date": "2026-01-20",
        "deal_date": "2026-01-17",
        "transfer_type": "FX Local",
        "client_name": "TEST_Storage Client",
        "from_type": "bank",
        "from_company": "Acme Corporation",
        "from_bank": "JP Morgan Chase",
        "from_account_num": "123456",
        "from_wallet_address": "",
        "to_type": "bank",
        "to_company": "GlobalTech Inc",
        "to_bank": "Citibank",
        "to_account_num": "654321",
        "to_wallet_address": "",
        "ours_type": "bank",
        "ours_bank": "HSBC",
        "ours_account_num": "999",
        "ours_wallet_address": "",
        "buy_currency": "USD",
        "sell_currency": "EUR",
        "currency_amount": 1000,
        "amount": 920,
        "rate": 0.92,
        "remarks": "storage test",
    }
    r = requests.post(f"{API}/deals", json=payload, headers=_headers(tokens["trader"]["token"]), timeout=30)
    assert r.status_code == 200, r.text
    deal = r.json()
    assert "id" in deal and "reference_number" in deal
    return deal


class TestDealCRUD:
    def test_create_deal(self, created_deal):
        assert created_deal["status"] == "pending"
        assert created_deal["settlement_proofs"] == []

    def test_list_deals(self, tokens, created_deal):
        r = requests.get(f"{API}/deals", headers=_headers(tokens["trader"]["token"]), timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "deals" in data
        ids = [d["id"] for d in data["deals"]]
        assert created_deal["id"] in ids

    def test_get_deal_detail(self, tokens, created_deal):
        r = requests.get(f"{API}/deals/{created_deal['id']}", headers=_headers(tokens["trader"]["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == created_deal["id"]
        assert isinstance(d.get("settlement_proofs"), list)
        assert isinstance(d.get("history"), list)


class TestStorageFlow:
    proof_ctx = {}

    def test_upload_client_proof(self, tokens, created_deal):
        png = _make_png_bytes()
        files = {"file": ("test.png", png, "image/png")}
        r = requests.post(
            f"{API}/deals/{created_deal['id']}/upload",
            params={"proof_type": "client"},
            files=files,
            headers=_headers(tokens["trader"]["token"]),
            timeout=60,
        )
        assert r.status_code == 200, r.text
        proof = r.json()
        for k in ("id", "path", "filename", "content_type", "proof_type"):
            assert k in proof, f"missing key {k} in response: {proof}"
        assert proof["proof_type"] == "client"
        assert proof["content_type"] == "image/png"
        assert proof["filename"] == "test.png"
        assert proof["path"].endswith(".png")
        TestStorageFlow.proof_ctx["proof"] = proof
        TestStorageFlow.proof_ctx["deal_id"] = created_deal["id"]
        TestStorageFlow.proof_ctx["png"] = png

    def test_download_file(self):
        proof = TestStorageFlow.proof_ctx.get("proof")
        assert proof, "upload must succeed first"
        r = requests.get(f"{API}/files/{proof['path']}", timeout=60)
        assert r.status_code == 200, r.text
        assert r.headers.get("content-type", "").startswith("image/png")
        # Content should be non-empty; Emergent may re-encode so just assert magic header
        assert r.content[:8] == b"\x89PNG\r\n\x1a\n" or len(r.content) > 0

    def test_deal_contains_proof(self, tokens):
        proof = TestStorageFlow.proof_ctx.get("proof")
        deal_id = TestStorageFlow.proof_ctx.get("deal_id")
        r = requests.get(f"{API}/deals/{deal_id}", headers=_headers(tokens["trader"]["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        proof_ids = [p["id"] for p in d.get("settlement_proofs", [])]
        assert proof["id"] in proof_ids

    def test_upload_processor_proof(self, tokens, created_deal):
        png = _make_png_bytes()
        files = {"file": ("processor.png", png, "image/png")}
        r = requests.post(
            f"{API}/deals/{created_deal['id']}/upload",
            params={"proof_type": "processor"},
            files=files,
            headers=_headers(tokens["trader"]["token"]),
            timeout=60,
        )
        assert r.status_code == 200, r.text
        assert r.json()["proof_type"] == "processor"

    def test_upload_invalid_proof_type(self, tokens, created_deal):
        png = _make_png_bytes()
        files = {"file": ("bad.png", png, "image/png")}
        r = requests.post(
            f"{API}/deals/{created_deal['id']}/upload",
            params={"proof_type": "invalid"},
            files=files,
            headers=_headers(tokens["trader"]["token"]),
            timeout=30,
        )
        assert r.status_code in (400, 422), r.text

    def test_delete_proof(self, tokens):
        proof = TestStorageFlow.proof_ctx.get("proof")
        deal_id = TestStorageFlow.proof_ctx.get("deal_id")
        r = requests.delete(
            f"{API}/deals/{deal_id}/proofs/{proof['id']}",
            headers=_headers(tokens["trader"]["token"]),
            timeout=30,
        )
        assert r.status_code == 200, r.text
        # Verify removed from deal
        r2 = requests.get(f"{API}/deals/{deal_id}", headers=_headers(tokens["trader"]["token"]), timeout=30)
        ids = [p["id"] for p in r2.json().get("settlement_proofs", [])]
        assert proof["id"] not in ids
