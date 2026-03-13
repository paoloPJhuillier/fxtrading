"""
Test file for Iteration 11 features:
1. hasLoaded pattern on pages (verified via UI tests, this tests backend API responses)
2. Proof of payment upload on NewDealPage
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBackendAPIs:
    """Test backend APIs are responding correctly for pages with hasLoaded pattern"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_deals_endpoint_response(self):
        """Test /api/deals endpoint returns paginated data quickly"""
        res = requests.get(f"{BASE_URL}/api/deals?page=1&limit=20", headers=self.headers)
        assert res.status_code == 200
        data = res.json()
        
        # Verify response structure
        assert "deals" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["deals"], list)
        print(f"Deals endpoint returned {len(data['deals'])} deals, total: {data['total']}")
    
    def test_deals_with_filters(self):
        """Test /api/deals with filters (used by hasLoaded pattern)"""
        # Test status filter
        res = requests.get(f"{BASE_URL}/api/deals?page=1&limit=20&status=pending", headers=self.headers)
        assert res.status_code == 200
        data = res.json()
        assert all(d['status'] == 'pending' for d in data['deals'])
        
        # Test client filter
        res = requests.get(f"{BASE_URL}/api/deals?page=1&limit=20&client=TEST", headers=self.headers)
        assert res.status_code == 200
        print(f"Filtered deals: {len(res.json()['deals'])} results")
    
    def test_treasury_deals_endpoint(self):
        """Test deals endpoint for treasury page (Deal Queue)"""
        # Login as treasury
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "treasury@fxtracker.com",
            "password": "Treasury@123"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/deals?page=1&limit=20", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "deals" in data
        print(f"Treasury deals: {data['total']} total")
    
    def test_users_endpoint(self):
        """Test users endpoint for UsersPage"""
        # Login as admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/users?page=1&limit=20", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "users" in data
        print(f"Users endpoint: {data['total']} users")
    
    def test_audit_logs_endpoint(self):
        """Test audit logs endpoint for AuditLogPage"""
        # Login as admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        assert login_res.status_code == 200
        token = login_res.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/audit-logs?page=1&limit=50", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "logs" in data
        print(f"Audit logs: {data['total']} entries")
    
    def test_reference_data_endpoints(self):
        """Test reference data endpoints for ReferenceDataPage"""
        endpoints = [
            "/api/reference/companies",
            "/api/reference/banks",
            "/api/reference/transaction-types",
            "/api/reference/transfer-types",
            "/api/reference/currencies"
        ]
        
        for endpoint in endpoints:
            res = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
            assert res.status_code == 200
            data = res.json()
            assert isinstance(data, list)
            print(f"{endpoint}: {len(data)} items")


class TestProofUpload:
    """Test proof of payment upload feature on NewDealPage"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as trader and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_deal_without_proof(self):
        """Test creating a deal without proof files - should work as before"""
        deal_data = {
            "client_name": "TEST_NoPoof_Client",
            "transaction_type": "Spot",
            "transfer_type": "FX Crypto Conversion",
            "deal_date": "2026-03-13",
            "value_date": "2026-03-13",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 1000,
            "amount": 920,
            "rate": 0.92,
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "12345",
            "to_type": "bank",
            "to_company": "Acme Corporation",
            "to_bank": "JP Morgan Chase",
            "to_account_num": "67890",
            "ours_type": "bank",
            "ours_bank": "JP Morgan Chase",
            "ours_account_num": "11111"
        }
        
        res = requests.post(f"{BASE_URL}/api/deals", json=deal_data, headers=self.headers)
        assert res.status_code == 200, f"Create deal failed: {res.text}"
        
        deal = res.json()
        assert "id" in deal
        assert deal["client_name"] == "TEST_NoPoof_Client"
        assert deal["settlement_proofs"] == [] or "settlement_proofs" not in deal
        print(f"Created deal without proof: {deal['reference_number']}")
        
        # Cleanup - store deal_id for possible cleanup
        self.deal_id_no_proof = deal["id"]
    
    def test_upload_proof_to_existing_deal(self):
        """Test uploading proof to an existing deal"""
        # First create a deal
        deal_data = {
            "client_name": "TEST_ProofTest_Client",
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "deal_date": "2026-03-13",
            "value_date": "2026-03-13",
            "buy_currency": "USD",
            "sell_currency": "PHP",
            "currency_amount": 5000,
            "amount": 290000,
            "rate": 58,
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "HSBC",
            "from_account_num": "PROOF123",
            "to_type": "bank",
            "to_company": "Acme Corporation",
            "to_bank": "HSBC",
            "to_account_num": "PROOF456",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "PROOF789"
        }
        
        create_res = requests.post(f"{BASE_URL}/api/deals", json=deal_data, headers=self.headers)
        assert create_res.status_code == 200, f"Create deal failed: {create_res.text}"
        deal_id = create_res.json()["id"]
        ref_num = create_res.json()["reference_number"]
        print(f"Created deal for proof test: {ref_num}")
        
        # Create a simple test file to upload
        import tempfile
        import io
        
        # Create a minimal PNG image (1x1 pixel transparent PNG)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89,  # Bit depth, color type, etc
            0x00, 0x00, 0x00, 0x0A, 0x49, 0x44, 0x41, 0x54,  # IDAT chunk
            0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x01,  # Compressed data
            0x0D, 0x0A, 0x2D, 0xB4,  # CRC
            0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
            0xAE, 0x42, 0x60, 0x82  # CRC
        ])
        
        files = {'file': ('test_proof.png', io.BytesIO(png_bytes), 'image/png')}
        upload_res = requests.post(
            f"{BASE_URL}/api/deals/{deal_id}/upload",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
        print(f"Uploaded proof to deal {ref_num}")
        
        # Verify the deal now has proof
        get_res = requests.get(f"{BASE_URL}/api/deals/{deal_id}", headers=self.headers)
        assert get_res.status_code == 200
        deal_data = get_res.json()
        
        assert "settlement_proofs" in deal_data
        assert len(deal_data["settlement_proofs"]) >= 1
        print(f"Deal now has {len(deal_data['settlement_proofs'])} proof(s)")
    
    def test_upload_endpoint_exists(self):
        """Verify the upload endpoint exists and accepts multipart form data"""
        # Create a deal first
        deal_data = {
            "client_name": "TEST_UploadEndpoint_Client",
            "transaction_type": "Spot",
            "transfer_type": "FX Crypto Conversion",
            "deal_date": "2026-03-13",
            "value_date": "2026-03-13",
            "buy_currency": "BTC",
            "sell_currency": "USD",
            "currency_amount": 1,
            "amount": 45000,
            "rate": 45000,
            "from_type": "crypto",
            "from_company": "Acme Corporation",
            "from_wallet_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "to_type": "bank",
            "to_company": "Acme Corporation",
            "to_bank": "JP Morgan Chase",
            "to_account_num": "99999",
            "ours_type": "crypto",
            "ours_wallet_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
        }
        
        create_res = requests.post(f"{BASE_URL}/api/deals", json=deal_data, headers=self.headers)
        assert create_res.status_code == 200
        deal_id = create_res.json()["id"]
        
        # Test that upload endpoint exists (even without a file)
        # This should fail with a 422 for missing file, not 404
        res = requests.post(
            f"{BASE_URL}/api/deals/{deal_id}/upload",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        # If 404, endpoint doesn't exist. If 422, it exists but needs file.
        assert res.status_code != 404, "Upload endpoint does not exist"
        print(f"Upload endpoint exists at /api/deals/{deal_id}/upload")


class TestTransactionHistoryEndpoint:
    """Test Transaction History page API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_deals_export_csv(self):
        """Test CSV export endpoint"""
        res = requests.get(f"{BASE_URL}/api/deals/export", headers=self.headers)
        assert res.status_code == 200
        assert 'text/csv' in res.headers.get('Content-Type', '') or len(res.content) > 0
        print(f"CSV export returned {len(res.content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
