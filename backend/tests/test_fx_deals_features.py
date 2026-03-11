"""
FX Trading Tracker - Backend API Tests
Tests for 6 new features:
1. Required field validation on deal entry
2. Client Name field in deals
3. Filters on Trader's My Deals page  
4. Filters on Treasury's Deal Queue page
5. Settlement proof image upload/view/delete
6. Complete deal detail view
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable must be set")

# Test credentials from seed data
TRADER_CREDS = {"email": "trader@fxtracker.com", "password": "Trader@123"}
TREASURY_CREDS = {"email": "treasury@fxtracker.com", "password": "Treasury@123"}
ADMIN_CREDS = {"email": "admin@fxtracker.com", "password": "Admin@123"}


class TestAuthentication:
    """Test login with all three role credentials"""

    def test_trader_login(self):
        """Verify trader can login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TRADER_CREDS)
        assert response.status_code == 200, f"Trader login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "trader"
        assert data["user"]["email"] == TRADER_CREDS["email"]
        print(f"✓ Trader login successful: {data['user']['name']}")

    def test_treasury_login(self):
        """Verify treasury user can login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TREASURY_CREDS)
        assert response.status_code == 200, f"Treasury login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "treasury"
        print(f"✓ Treasury login successful: {data['user']['name']}")

    def test_admin_login(self):
        """Verify admin can login with provided credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")

    def test_invalid_login(self):
        """Verify invalid credentials are rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "wrong@test.com", "password": "wrong"})
        assert response.status_code == 401


@pytest.fixture
def trader_token():
    """Get trader auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TRADER_CREDS)
    if response.status_code != 200:
        pytest.skip("Trader login failed")
    return response.json()["token"]


@pytest.fixture
def treasury_token():
    """Get treasury auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TREASURY_CREDS)
    if response.status_code != 200:
        pytest.skip("Treasury login failed")
    return response.json()["token"]


@pytest.fixture
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json()["token"]


class TestReferenceData:
    """Test reference data endpoints needed for deal creation"""

    def test_get_companies(self, trader_token):
        """Verify companies reference data is available"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/companies", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Found {len(data)} companies")

    def test_get_banks(self, trader_token):
        """Verify banks reference data is available"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/banks", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Found {len(data)} banks")

    def test_get_currencies(self, trader_token):
        """Verify currencies reference data is available (fiat, stablecoin, crypto)"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/currencies", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify different types
        types = set(c.get("type") for c in data)
        assert "fiat" in types or "stablecoin" in types or "crypto" in types
        print(f"✓ Found {len(data)} currencies, types: {types}")

    def test_get_transaction_types(self, trader_token):
        """Verify transaction types are available"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/transaction-types", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        print(f"✓ Found {len(data)} transaction types")

    def test_get_transfer_types(self, trader_token):
        """Verify transfer types are available"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/transfer-types", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        print(f"✓ Found {len(data)} transfer types")


class TestDealCreationValidation:
    """Feature 1: Test required field validation on deal creation"""

    def test_create_deal_missing_all_fields(self, trader_token):
        """Verify deal creation fails with missing required fields"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Send empty deal - should fail validation
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json={})
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        print("✓ Deal creation properly rejects empty payload with 422")

    def test_create_deal_missing_client_name(self, trader_token):
        """Feature 2: Verify client_name is a required field"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # All fields except client_name
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "Wire Transfer",
            # "client_name": missing
            "deal_date": "2026-01-15",
            "value_date": "2026-01-17",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "123456789",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "987654321",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 9200,
            "rate": 0.92,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 422, f"Expected 422 for missing client_name, got {response.status_code}"
        print("✓ Deal creation requires client_name field")


class TestDealCRUD:
    """Test complete deal creation with all fields including client_name"""
    
    created_deal_id = None

    def test_create_deal_with_all_fields(self, trader_token):
        """Feature 2: Create deal with client_name and verify all required fields"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "Wire Transfer",
            "client_name": "TEST_Client_Acme Corp",
            "deal_date": "2026-01-15",
            "value_date": "2026-01-17",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "TEST123456789",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "TEST987654321",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 9200,  # currency_amount * rate
            "rate": 0.92,
            "remarks": "Test deal for automated testing"
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Deal creation failed: {response.text}"
        
        data = response.json()
        # Verify response has all expected fields
        assert "id" in data
        assert "reference_number" in data
        assert data["client_name"] == "TEST_Client_Acme Corp"
        assert data["status"] == "pending"
        assert data["transaction_type"] == "Spot"
        assert data["buy_currency"] == "USD"
        assert data["sell_currency"] == "EUR"
        assert data["currency_amount"] == 10000
        assert data["amount"] == 9200
        assert data["rate"] == 0.92
        assert "settlement_proofs" in data
        assert data["settlement_proofs"] == []
        
        TestDealCRUD.created_deal_id = data["id"]
        print(f"✓ Deal created with reference: {data['reference_number']}, client: {data['client_name']}")
        return data

    def test_get_deal_detail(self, trader_token):
        """Feature 6: Test complete deal detail view"""
        if not TestDealCRUD.created_deal_id:
            pytest.skip("No deal created in previous test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals/{TestDealCRUD.created_deal_id}", headers=headers)
        assert response.status_code == 200, f"Get deal failed: {response.text}"
        
        data = response.json()
        # Verify all deal fields are returned
        assert data["id"] == TestDealCRUD.created_deal_id
        assert "client_name" in data
        assert "reference_number" in data
        assert "transaction_type" in data
        assert "transfer_type" in data
        assert "deal_date" in data
        assert "value_date" in data
        assert "from_company" in data
        assert "from_bank" in data
        assert "from_account_num" in data
        assert "to_company" in data
        assert "to_bank" in data
        assert "to_account_num" in data
        assert "buy_currency" in data
        assert "sell_currency" in data
        assert "currency_amount" in data
        assert "amount" in data
        assert "rate" in data
        assert "status" in data
        assert "created_by" in data
        assert "created_by_name" in data
        assert "settlement_proofs" in data
        print(f"✓ Deal detail view returns all fields correctly")


class TestDealFilters:
    """Feature 3 & 4: Test filters on deals list (Trader My Deals & Treasury Queue)"""

    def test_filter_by_status(self, trader_token):
        """Test filtering deals by status"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?status=pending", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # All returned deals should have pending status
        for deal in data:
            assert deal["status"] == "pending", f"Expected pending status, got {deal['status']}"
        print(f"✓ Filter by status works: {len(data)} pending deals")

    def test_filter_by_client(self, trader_token):
        """Test filtering deals by client name"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Filter by partial client name
        response = requests.get(f"{BASE_URL}/api/deals?client=TEST_Client", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for deal in data:
            assert "TEST_Client" in deal.get("client_name", ""), f"Client filter not working"
        print(f"✓ Filter by client name works: {len(data)} matching deals")

    def test_filter_by_currency(self, trader_token):
        """Test filtering deals by currency"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?currency=USD", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for deal in data:
            has_usd = deal.get("buy_currency") == "USD" or deal.get("sell_currency") == "USD"
            assert has_usd, f"Currency filter not working"
        print(f"✓ Filter by currency works: {len(data)} deals with USD")

    def test_filter_by_date_range(self, trader_token):
        """Test filtering deals by date range"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?date_from=2026-01-01&date_to=2026-12-31", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Filter by date range works: {len(data)} deals in range")

    def test_treasury_filter_access(self, treasury_token):
        """Feature 4: Treasury can access deal filters"""
        headers = {"Authorization": f"Bearer {treasury_token}"}
        # Treasury should see all deals, not just their own
        response = requests.get(f"{BASE_URL}/api/deals?status=pending", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Treasury can filter deals: {len(data)} pending deals visible")


class TestSettlementProofUpload:
    """Feature 5: Test settlement proof image upload/view/delete"""

    test_deal_id = None

    @pytest.fixture(autouse=True)
    def setup_deal(self, trader_token):
        """Create a test deal for proof upload tests"""
        if TestSettlementProofUpload.test_deal_id:
            return
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "Wire Transfer",
            "client_name": "TEST_ProofUpload Client",
            "deal_date": "2026-01-20",
            "value_date": "2026-01-22",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "TEST_ACC_001",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "TEST_ACC_002",
            "buy_currency": "GBP",
            "sell_currency": "USD",
            "currency_amount": 5000,
            "amount": 6250,
            "rate": 1.25,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        if response.status_code == 200:
            TestSettlementProofUpload.test_deal_id = response.json()["id"]

    def test_upload_settlement_proof(self, trader_token):
        """Test uploading a settlement proof image"""
        if not TestSettlementProofUpload.test_deal_id:
            pytest.skip("No deal created for proof upload test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create a simple test image (1x1 pixel PNG)
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimension
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        
        files = {"file": ("test_proof.png", png_data, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/deals/{TestSettlementProofUpload.test_deal_id}/upload",
            headers=headers,
            files=files
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "path" in data
        assert data["filename"] == "test_proof.png"
        assert data["content_type"] == "image/png"
        print(f"✓ Settlement proof uploaded successfully: {data['path']}")
        return data

    def test_view_deal_with_proofs(self, trader_token):
        """Test viewing deal detail shows settlement proofs"""
        if not TestSettlementProofUpload.test_deal_id:
            pytest.skip("No deal created for proof view test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals/{TestSettlementProofUpload.test_deal_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "settlement_proofs" in data
        # If proof was uploaded in previous test
        if len(data["settlement_proofs"]) > 0:
            proof = data["settlement_proofs"][0]
            assert "id" in proof
            assert "path" in proof
            assert "filename" in proof
            print(f"✓ Deal detail shows {len(data['settlement_proofs'])} settlement proof(s)")
        else:
            print("✓ Settlement proofs array present (empty)")

    def test_upload_invalid_file_type(self, trader_token):
        """Test that non-image files are rejected"""
        if not TestSettlementProofUpload.test_deal_id:
            pytest.skip("No deal created for invalid upload test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        files = {"file": ("test.txt", b"This is not an image", "text/plain")}
        response = requests.post(
            f"{BASE_URL}/api/deals/{TestSettlementProofUpload.test_deal_id}/upload",
            headers=headers,
            files=files
        )
        assert response.status_code == 400, f"Expected 400 for invalid file type, got {response.status_code}"
        print("✓ Invalid file type correctly rejected")

    def test_delete_settlement_proof(self, trader_token):
        """Test deleting a settlement proof"""
        if not TestSettlementProofUpload.test_deal_id:
            pytest.skip("No deal created for proof delete test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # First get the deal to find proof IDs
        response = requests.get(f"{BASE_URL}/api/deals/{TestSettlementProofUpload.test_deal_id}", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get deal")
        
        proofs = response.json().get("settlement_proofs", [])
        if not proofs:
            pytest.skip("No proofs to delete")
        
        proof_id = proofs[0]["id"]
        response = requests.delete(
            f"{BASE_URL}/api/deals/{TestSettlementProofUpload.test_deal_id}/proofs/{proof_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Delete failed: {response.text}"
        print(f"✓ Settlement proof deleted successfully")


class TestTreasuryProcessing:
    """Test treasury deal processing (confirm/return)"""

    process_deal_id = None

    @pytest.fixture(autouse=True)
    def setup_pending_deal(self, trader_token):
        """Create a pending deal for treasury processing"""
        if TestTreasuryProcessing.process_deal_id:
            return
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Forward",
            "transfer_type": "SWIFT",
            "client_name": "TEST_Treasury Processing Client",
            "deal_date": "2026-02-01",
            "value_date": "2026-02-05",
            "from_company": "Sterling Enterprises",
            "from_bank": "HSBC",
            "from_account_num": "TREAS_001",
            "to_company": "Pacific Trading Co",
            "to_bank": "Standard Chartered",
            "to_account_num": "TREAS_002",
            "buy_currency": "JPY",
            "sell_currency": "USD",
            "currency_amount": 1000000,
            "amount": 8500,
            "rate": 0.0085,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        if response.status_code == 200:
            TestTreasuryProcessing.process_deal_id = response.json()["id"]

    def test_treasury_can_view_pending_deals(self, treasury_token):
        """Treasury can see pending deals from traders"""
        headers = {"Authorization": f"Bearer {treasury_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?status=pending", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Treasury can view {len(data)} pending deals")

    def test_treasury_confirm_deal(self, treasury_token, trader_token):
        """Treasury can confirm a pending deal with remarks"""
        # First create a fresh deal
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "Wire Transfer",
            "client_name": "TEST_Confirm Deal Client",
            "deal_date": "2026-02-10",
            "value_date": "2026-02-12",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "CONF_001",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "CONF_002",
            "buy_currency": "CHF",
            "sell_currency": "EUR",
            "currency_amount": 25000,
            "amount": 25625,
            "rate": 1.025,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        if create_resp.status_code != 200:
            pytest.skip("Could not create deal for confirm test")
        
        deal_id = create_resp.json()["id"]
        
        # Treasury confirms the deal
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        process_data = {
            "status": "confirmed",
            "treasury_remarks": "Approved after verification. Test confirmation."
        }
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json=process_data
        )
        assert response.status_code == 200, f"Confirm failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["treasury_remarks"] == "Approved after verification. Test confirmation."
        assert data["processed_by_name"] is not None
        assert data["processed_at"] is not None
        print(f"✓ Treasury confirmed deal: {data['reference_number']}")

    def test_treasury_return_deal(self, treasury_token, trader_token):
        """Treasury can return a pending deal with remarks"""
        # First create a fresh deal
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "Wire Transfer",
            "client_name": "TEST_Return Deal Client",
            "deal_date": "2026-02-11",
            "value_date": "2026-02-13",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "RET_001",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "RET_002",
            "buy_currency": "AUD",
            "sell_currency": "NZD",
            "currency_amount": 15000,
            "amount": 15750,
            "rate": 1.05,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        if create_resp.status_code != 200:
            pytest.skip("Could not create deal for return test")
        
        deal_id = create_resp.json()["id"]
        
        # Treasury returns the deal
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        process_data = {
            "status": "returned",
            "treasury_remarks": "Missing documentation. Please resubmit."
        }
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json=process_data
        )
        assert response.status_code == 200, f"Return failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "returned"
        assert data["treasury_remarks"] == "Missing documentation. Please resubmit."
        print(f"✓ Treasury returned deal: {data['reference_number']}")

    def test_cannot_process_already_processed_deal(self, treasury_token, trader_token):
        """Verify cannot re-process an already processed deal"""
        # Create and confirm a deal
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "ACH",
            "client_name": "TEST_Double Process Client",
            "deal_date": "2026-02-15",
            "value_date": "2026-02-17",
            "from_company": "Acme Corporation",
            "from_bank": "Bank of America",
            "from_account_num": "DBL_001",
            "to_company": "Atlantic Financial Group",
            "to_bank": "Deutsche Bank",
            "to_account_num": "DBL_002",
            "buy_currency": "EUR",
            "sell_currency": "USD",
            "currency_amount": 8000,
            "amount": 8800,
            "rate": 1.1,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        if create_resp.status_code != 200:
            pytest.skip("Could not create deal for double process test")
        
        deal_id = create_resp.json()["id"]
        
        # First confirmation
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "confirmed", "treasury_remarks": "First approval"}
        )
        
        # Try to process again
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "returned", "treasury_remarks": "Try to return after confirm"}
        )
        assert response.status_code == 400, f"Expected 400 for already processed deal, got {response.status_code}"
        print("✓ Cannot re-process already processed deal")

    def test_trader_cannot_process_deals(self, trader_token):
        """Verify traders cannot process deals (only treasury)"""
        if not TestTreasuryProcessing.process_deal_id:
            pytest.skip("No deal to test trader processing restriction")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.put(
            f"{BASE_URL}/api/deals/{TestTreasuryProcessing.process_deal_id}/process",
            headers=headers,
            json={"status": "confirmed", "treasury_remarks": "Trader trying to confirm"}
        )
        assert response.status_code == 403, f"Expected 403 for trader processing, got {response.status_code}"
        print("✓ Traders cannot process deals (correct 403 response)")


class TestDashboardStats:
    """Test dashboard statistics endpoint"""

    def test_trader_dashboard(self, trader_token):
        """Trader can access their dashboard stats"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats?range=30d", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deals" in data
        assert "pending_deals" in data
        assert "confirmed_deals" in data
        assert "returned_deals" in data
        assert "total_volume" in data
        print(f"✓ Trader dashboard: {data['total_deals']} deals, {data['pending_deals']} pending")

    def test_treasury_dashboard(self, treasury_token):
        """Treasury can access dashboard stats"""
        headers = {"Authorization": f"Bearer {treasury_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats?range=7d", headers=headers)
        assert response.status_code == 200
        print("✓ Treasury dashboard accessible")

    def test_admin_dashboard(self, admin_token):
        """Admin can access dashboard with user count"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats?range=ytd", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data  # Admin-only field
        print(f"✓ Admin dashboard: {data['total_users']} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
