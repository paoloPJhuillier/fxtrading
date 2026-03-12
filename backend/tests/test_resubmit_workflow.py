"""
FX Trading Tracker - Return-Resubmit Workflow Tests
Tests for the complete return-resubmit cycle:
1. Trader creates deal with proof of payment
2. Treasury returns deal with remarks
3. Trader sees returned deal
4. Trader uploads new proof / deletes old proof
5. Trader resubmits deal (status back to pending)
6. Treasury re-reviews and confirms
7. Audit trail logs deal_resubmitted action
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable must be set")

# Test credentials
TRADER_CREDS = {"email": "trader@fxtracker.com", "password": "Trader@123"}
TREASURY_CREDS = {"email": "treasury@fxtracker.com", "password": "Treasury@123"}
ADMIN_CREDS = {"email": "admin@fxtracker.com", "password": "Admin@123"}


@pytest.fixture(scope="module")
def trader_token():
    """Get trader auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TRADER_CREDS)
    if response.status_code != 200:
        pytest.skip("Trader login failed")
    return response.json()["token"]


@pytest.fixture(scope="module")
def treasury_token():
    """Get treasury auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TREASURY_CREDS)
    if response.status_code != 200:
        pytest.skip("Treasury login failed")
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json()["token"]


# PNG test data for proof uploads
PNG_DATA = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
    0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82
])


class TestCompleteResubmitWorkflow:
    """Test full return-resubmit workflow end to end"""
    
    deal_id = None
    deal_reference = None
    proof_id = None
    
    def test_01_trader_creates_deal_with_proof(self, trader_token):
        """Step 1: Trader creates deal and uploads proof of payment"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Resubmit_Client",
            "deal_date": "2026-01-20",
            "value_date": "2026-01-22",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "RESUBMIT_001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "RESUBMIT_002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "OURS_001",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 9200,
            "rate": 0.92,
            "remarks": "Test deal for resubmit workflow"
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Deal creation failed: {response.text}"
        
        data = response.json()
        TestCompleteResubmitWorkflow.deal_id = data["id"]
        TestCompleteResubmitWorkflow.deal_reference = data["reference_number"]
        
        assert data["status"] == "pending"
        print(f"✓ Deal created: {data['reference_number']} with status: pending")
        
        # Upload proof of payment
        files = {"file": ("initial_proof.png", PNG_DATA, "image/png")}
        upload_resp = requests.post(
            f"{BASE_URL}/api/deals/{data['id']}/upload",
            headers=headers,
            files=files
        )
        assert upload_resp.status_code == 200, f"Proof upload failed: {upload_resp.text}"
        
        proof_data = upload_resp.json()
        TestCompleteResubmitWorkflow.proof_id = proof_data["id"]
        print(f"✓ Initial proof of payment uploaded: {proof_data['filename']}")
    
    def test_02_deal_shows_in_treasury_queue_as_pending(self, treasury_token):
        """Step 2: Deal shows in Treasury queue with pending status"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {treasury_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?status=pending", headers=headers)
        assert response.status_code == 200
        
        deals = response.json()
        found = any(d["id"] == TestCompleteResubmitWorkflow.deal_id for d in deals)
        assert found, "Deal not found in treasury pending queue"
        print(f"✓ Deal found in Treasury pending queue")
    
    def test_03_treasury_returns_deal_with_remarks(self, treasury_token):
        """Step 3: Treasury returns deal with remarks explaining why proof is unacceptable"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {treasury_token}"}
        process_data = {
            "status": "returned",
            "treasury_remarks": "Proof of payment image is too blurry. Please upload a clearer image showing the transaction reference."
        }
        response = requests.put(
            f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}/process",
            headers=headers,
            json=process_data
        )
        assert response.status_code == 200, f"Return failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "returned"
        assert data["treasury_remarks"] == process_data["treasury_remarks"]
        assert data["processed_by"] is not None
        assert data["processed_by_name"] is not None
        assert data["processed_at"] is not None
        print(f"✓ Treasury returned deal with remarks")
    
    def test_04_trader_sees_returned_deal_with_remarks(self, trader_token):
        """Step 4: Trader can see the returned deal with treasury remarks"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "returned"
        assert "blurry" in data["treasury_remarks"].lower()
        assert data["processed_by_name"] is not None
        print(f"✓ Trader sees returned deal with remarks: '{data['treasury_remarks'][:50]}...'")
    
    def test_05_trader_deletes_old_proof(self, trader_token):
        """Step 5a: Trader can delete old proof on returned deal"""
        if not TestCompleteResubmitWorkflow.deal_id or not TestCompleteResubmitWorkflow.proof_id:
            pytest.skip("No deal or proof to test")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.delete(
            f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}/proofs/{TestCompleteResubmitWorkflow.proof_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Delete proof failed: {response.text}"
        print(f"✓ Old proof deleted successfully")
        
        # Verify proof is deleted
        deal_resp = requests.get(f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}", headers=headers)
        proofs = deal_resp.json().get("settlement_proofs", [])
        found = any(p["id"] == TestCompleteResubmitWorkflow.proof_id for p in proofs)
        assert not found, "Proof should have been deleted"
        print(f"✓ Proof deletion verified")
    
    def test_06_trader_uploads_new_proof(self, trader_token):
        """Step 5b: Trader can upload new proof on returned deal"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        files = {"file": ("better_proof.png", PNG_DATA, "image/png")}
        response = requests.post(
            f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}/upload",
            headers=headers,
            files=files
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        proof_data = response.json()
        assert proof_data["filename"] == "better_proof.png"
        print(f"✓ New (better) proof uploaded: {proof_data['filename']}")
    
    def test_07_resubmit_clears_treasury_fields(self, trader_token):
        """Step 6: Trader resubmits deal - status becomes pending, treasury fields cleared"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Call resubmit endpoint
        response = requests.put(
            f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}/resubmit",
            headers=headers
        )
        assert response.status_code == 200, f"Resubmit failed: {response.text}"
        
        data = response.json()
        # Verify status changed to pending
        assert data["status"] == "pending", f"Expected status 'pending', got '{data['status']}'"
        # Verify treasury_remarks cleared
        assert data["treasury_remarks"] == "", f"treasury_remarks should be empty, got '{data['treasury_remarks']}'"
        # Verify processed_by cleared
        assert data["processed_by"] is None, f"processed_by should be None, got '{data['processed_by']}'"
        # Verify processed_by_name cleared
        assert data["processed_by_name"] is None, f"processed_by_name should be None"
        # Verify processed_at cleared
        assert data["processed_at"] is None, f"processed_at should be None"
        
        print(f"✓ Deal resubmitted successfully:")
        print(f"  - Status: {data['status']}")
        print(f"  - treasury_remarks cleared: {data['treasury_remarks'] == ''}")
        print(f"  - processed_by cleared: {data['processed_by'] is None}")
    
    def test_08_resubmitted_deal_appears_in_treasury_queue(self, treasury_token):
        """Step 7: Resubmitted deal appears in Treasury queue as pending"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {treasury_token}"}
        response = requests.get(f"{BASE_URL}/api/deals?status=pending", headers=headers)
        assert response.status_code == 200
        
        deals = response.json()
        found = any(d["id"] == TestCompleteResubmitWorkflow.deal_id for d in deals)
        assert found, "Resubmitted deal not found in treasury pending queue"
        print(f"✓ Resubmitted deal found in Treasury queue again")
    
    def test_09_treasury_confirms_resubmitted_deal(self, treasury_token):
        """Step 8: Treasury re-reviews and confirms the resubmitted deal"""
        if not TestCompleteResubmitWorkflow.deal_id:
            pytest.skip("No deal created")
        
        headers = {"Authorization": f"Bearer {treasury_token}"}
        process_data = {
            "status": "confirmed",
            "treasury_remarks": "New proof of payment is acceptable. Deal confirmed."
        }
        response = requests.put(
            f"{BASE_URL}/api/deals/{TestCompleteResubmitWorkflow.deal_id}/process",
            headers=headers,
            json=process_data
        )
        assert response.status_code == 200, f"Confirm failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["processed_by_name"] is not None
        print(f"✓ Treasury confirmed resubmitted deal")
    
    def test_10_audit_trail_logs_resubmit_action(self, admin_token):
        """Step 9: Verify audit trail logs 'deal_resubmitted' action"""
        if not TestCompleteResubmitWorkflow.deal_reference:
            pytest.skip("No deal reference")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?action=deal_resubmitted",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        logs = data.get("logs", [])
        
        # Find the resubmit log for our deal
        found = any(
            log["action"] == "deal_resubmitted" and 
            log["entity_ref"] == TestCompleteResubmitWorkflow.deal_reference
            for log in logs
        )
        assert found, "deal_resubmitted action not found in audit logs"
        
        # Verify log structure
        for log in logs:
            if log["action"] == "deal_resubmitted" and log["entity_ref"] == TestCompleteResubmitWorkflow.deal_reference:
                assert log["entity_type"] == "deal"
                assert "resubmitted" in log["details"].lower()
                print(f"✓ Audit trail logged 'deal_resubmitted' action:")
                print(f"  - User: {log['user_name']}")
                print(f"  - Details: {log['details']}")
                break


class TestResubmitEndpointValidation:
    """Test resubmit endpoint validation rules"""
    
    def test_resubmit_only_works_for_returned_deals_not_pending(self, trader_token):
        """PUT /api/deals/{id}/resubmit returns 400 for pending deals"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create a new pending deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Pending_Resubmit",
            "deal_date": "2026-01-25",
            "value_date": "2026-01-27",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "PEND_001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "PEND_002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "PEND_003",
            "buy_currency": "GBP",
            "sell_currency": "USD",
            "currency_amount": 5000,
            "amount": 6250,
            "rate": 1.25,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        
        # Try to resubmit a pending deal (should fail with 400)
        response = requests.put(f"{BASE_URL}/api/deals/{deal_id}/resubmit", headers=headers)
        assert response.status_code == 400, f"Expected 400 for pending deal, got {response.status_code}"
        assert "returned" in response.json().get("detail", "").lower()
        print(f"✓ Resubmit correctly rejects pending deals with 400")
    
    def test_resubmit_only_works_for_returned_deals_not_confirmed(self, trader_token, treasury_token):
        """PUT /api/deals/{id}/resubmit returns 400 for confirmed deals"""
        # Create and confirm a deal
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Confirmed_Resubmit",
            "deal_date": "2026-01-26",
            "value_date": "2026-01-28",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "CONF_R001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "CONF_R002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "CONF_R003",
            "buy_currency": "CHF",
            "sell_currency": "EUR",
            "currency_amount": 8000,
            "amount": 8640,
            "rate": 1.08,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        
        # Confirm the deal
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "confirmed", "treasury_remarks": "Approved for test"}
        )
        
        # Try to resubmit confirmed deal (should fail with 400)
        response = requests.put(f"{BASE_URL}/api/deals/{deal_id}/resubmit", headers=headers_trader)
        assert response.status_code == 400, f"Expected 400 for confirmed deal, got {response.status_code}"
        print(f"✓ Resubmit correctly rejects confirmed deals with 400")
    
    def test_resubmit_only_works_for_returned_deals_not_cancelled(self, trader_token):
        """PUT /api/deals/{id}/resubmit returns 400 for cancelled deals"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create and cancel a deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Cancelled_Resubmit",
            "deal_date": "2026-01-27",
            "value_date": "2026-01-29",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "CANC_R001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "CANC_R002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "CANC_R003",
            "buy_currency": "AUD",
            "sell_currency": "NZD",
            "currency_amount": 3000,
            "amount": 3150,
            "rate": 1.05,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        
        # Cancel the deal
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "Test cancellation"}
        )
        
        # Try to resubmit cancelled deal (should fail with 400)
        response = requests.put(f"{BASE_URL}/api/deals/{deal_id}/resubmit", headers=headers)
        assert response.status_code == 400, f"Expected 400 for cancelled deal, got {response.status_code}"
        print(f"✓ Resubmit correctly rejects cancelled deals with 400")
    
    def test_resubmit_only_works_for_own_deals(self, trader_token, treasury_token):
        """PUT /api/deals/{id}/resubmit returns 403 for other's deals"""
        # Create deal as trader
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_OwnDeal_Resubmit",
            "deal_date": "2026-01-28",
            "value_date": "2026-01-30",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "OWN_R001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "OWN_R002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "OWN_R003",
            "buy_currency": "JPY",
            "sell_currency": "USD",
            "currency_amount": 100000,
            "amount": 850,
            "rate": 0.0085,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        
        # Return the deal via treasury
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "returned", "treasury_remarks": "Test return for ownership test"}
        )
        
        # Treasury tries to resubmit (should fail with 403 - only trader role can, but also must be owner)
        response = requests.put(f"{BASE_URL}/api/deals/{deal_id}/resubmit", headers=headers_treasury)
        assert response.status_code == 403, f"Expected 403 for non-owner/non-trader, got {response.status_code}"
        print(f"✓ Resubmit correctly rejects non-owner with 403")


class TestProofUploadVisibility:
    """Test that upload proof button is only visible for pending/returned deals"""
    
    def test_upload_allowed_for_pending_deal(self, trader_token):
        """Upload proof works for pending deals"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create pending deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Upload_Pending",
            "deal_date": "2026-02-01",
            "value_date": "2026-02-03",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "UP_001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "UP_002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "UP_003",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 1000,
            "amount": 920,
            "rate": 0.92,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Upload should work
        files = {"file": ("pending_proof.png", PNG_DATA, "image/png")}
        response = requests.post(f"{BASE_URL}/api/deals/{deal_id}/upload", headers=headers, files=files)
        assert response.status_code == 200
        print(f"✓ Upload proof works for pending deals")
    
    def test_upload_allowed_for_returned_deal(self, trader_token, treasury_token):
        """Upload proof works for returned deals"""
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        
        # Create and return a deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Upload_Returned",
            "deal_date": "2026-02-02",
            "value_date": "2026-02-04",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "UPR_001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "UPR_002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "UPR_003",
            "buy_currency": "GBP",
            "sell_currency": "USD",
            "currency_amount": 2000,
            "amount": 2500,
            "rate": 1.25,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Return the deal
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "returned", "treasury_remarks": "Test return"}
        )
        
        # Upload should work for returned deal
        files = {"file": ("returned_proof.png", PNG_DATA, "image/png")}
        response = requests.post(f"{BASE_URL}/api/deals/{deal_id}/upload", headers=headers_trader, files=files)
        assert response.status_code == 200
        print(f"✓ Upload proof works for returned deals")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
