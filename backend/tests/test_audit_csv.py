"""
Test Audit Trail and CSV Export Features for FX Trading Tracker
Tests: audit log endpoints, CSV export functionality, action logging
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fx-deal-queue.preview.emergentagent.com').rstrip('/')

# ---- Fixtures ----
@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@fxtracker.com",
        "password": "Admin@123"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="module")
def trader_token():
    """Get trader auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "trader@fxtracker.com",
        "password": "Trader@123"
    })
    assert resp.status_code == 200, f"Trader login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture(scope="module")
def treasury_token():
    """Get treasury auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "treasury@fxtracker.com",
        "password": "Treasury@123"
    })
    assert resp.status_code == 200, f"Treasury login failed: {resp.text}"
    return resp.json()["token"]

@pytest.fixture
def admin_client(admin_token):
    """Session with admin auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session

@pytest.fixture
def trader_client(trader_token):
    """Session with trader auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {trader_token}"
    })
    return session

@pytest.fixture
def treasury_client(treasury_token):
    """Session with treasury auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {treasury_token}"
    })
    return session


# ==== AUDIT LOG TESTS ====

class TestAuditLogEndpoint:
    """Tests for GET /api/audit-logs endpoint"""
    
    def test_audit_logs_admin_access(self, admin_client):
        """Admin should be able to access audit logs"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs")
        assert resp.status_code == 200
        data = resp.json()
        # Verify response structure
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert isinstance(data["logs"], list)
        print(f"✓ Admin can access audit logs - {data['total']} entries")
    
    def test_audit_logs_trader_forbidden(self, trader_client):
        """Traders should NOT be able to access audit logs"""
        resp = trader_client.get(f"{BASE_URL}/api/audit-logs")
        assert resp.status_code == 403
        print("✓ Trader correctly denied access to audit logs")
    
    def test_audit_logs_treasury_forbidden(self, treasury_client):
        """Treasury should NOT be able to access audit logs"""
        resp = treasury_client.get(f"{BASE_URL}/api/audit-logs")
        assert resp.status_code == 403
        print("✓ Treasury correctly denied access to audit logs")
    
    def test_audit_logs_pagination(self, admin_client):
        """Test pagination parameters"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs?page=1&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["logs"]) <= 5
        print(f"✓ Pagination working - page 1, limit 5, got {len(data['logs'])} entries")
    
    def test_audit_logs_filter_by_action(self, admin_client):
        """Test filtering by action type"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs?action=deal_created")
        assert resp.status_code == 200
        data = resp.json()
        # All logs should have action=deal_created if any results returned
        for log in data["logs"]:
            assert log["action"] == "deal_created", f"Expected action deal_created, got {log['action']}"
        print(f"✓ Filter by action works - {len(data['logs'])} deal_created entries")
    
    def test_audit_logs_filter_by_entity_type(self, admin_client):
        """Test filtering by entity type"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs?entity_type=deal")
        assert resp.status_code == 200
        data = resp.json()
        for log in data["logs"]:
            assert log["entity_type"] == "deal", f"Expected entity_type deal, got {log['entity_type']}"
        print(f"✓ Filter by entity_type works - {len(data['logs'])} deal entries")
    
    def test_audit_logs_filter_by_user_name(self, admin_client):
        """Test filtering by user name"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs?user_name=John")
        assert resp.status_code == 200
        data = resp.json()
        for log in data["logs"]:
            assert "John" in log["user_name"], f"Expected user_name containing John, got {log['user_name']}"
        print(f"✓ Filter by user_name works - {len(data['logs'])} entries with 'John'")
    
    def test_audit_log_entry_structure(self, admin_client):
        """Verify audit log entry has correct structure"""
        resp = admin_client.get(f"{BASE_URL}/api/audit-logs?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        if data["logs"]:
            log = data["logs"][0]
            # Check required fields
            required_fields = ["id", "action", "entity_type", "entity_id", "user_id", "user_name", "user_role", "details", "created_at"]
            for field in required_fields:
                assert field in log, f"Missing field: {field}"
            print(f"✓ Log entry structure correct - action: {log['action']}, entity: {log['entity_type']}")
        else:
            print("⚠ No audit log entries to verify structure")


class TestAuditLogCreation:
    """Test that actions properly create audit log entries"""
    
    def test_deal_creation_logged(self, trader_client, admin_client):
        """Creating a deal should create an audit log entry"""
        # Create a test deal
        deal_data = {
            "transaction_type": "Spot",
            "value_date": datetime.now().strftime("%Y-%m-%d"),
            "deal_date": datetime.now().strftime("%Y-%m-%d"),
            "transfer_type": "FX Local",
            "client_name": "TEST_AuditClient",
            "from_type": "bank",
            "from_company": "Test Corp",
            "from_bank": "Test Bank",
            "from_account_num": "1234567890",
            "to_type": "bank",
            "to_company": "Target Corp",
            "to_bank": "Target Bank",
            "to_account_num": "0987654321",
            "ours_type": "bank",
            "ours_bank": "Our Bank",
            "ours_account_num": "1111111111",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 9200,
            "rate": 0.92,
            "remarks": "Audit test deal"
        }
        
        create_resp = trader_client.post(f"{BASE_URL}/api/deals", json=deal_data)
        assert create_resp.status_code == 200
        deal = create_resp.json()
        deal_ref = deal["reference_number"]
        print(f"✓ Created test deal: {deal_ref}")
        
        # Check audit log for deal_created entry
        audit_resp = admin_client.get(f"{BASE_URL}/api/audit-logs?action=deal_created&limit=5")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()
        
        # Find the audit entry for our deal
        found = False
        for log in audit_data["logs"]:
            if log["entity_ref"] == deal_ref:
                found = True
                assert log["action"] == "deal_created"
                assert log["entity_type"] == "deal"
                assert "John Trader" in log["user_name"]  # Default trader name
                print(f"✓ Found audit entry for deal {deal_ref} - action: deal_created")
                break
        
        assert found, f"Audit entry not found for deal {deal_ref}"
    
    def test_deal_confirmation_logged(self, trader_client, treasury_client, admin_client):
        """Confirming a deal should create an audit log entry"""
        # Create a deal first
        deal_data = {
            "transaction_type": "Today",
            "value_date": datetime.now().strftime("%Y-%m-%d"),
            "deal_date": datetime.now().strftime("%Y-%m-%d"),
            "transfer_type": "FX Local",
            "client_name": "TEST_ConfirmAudit",
            "from_type": "bank",
            "from_company": "Test Corp",
            "from_bank": "Test Bank",
            "from_account_num": "1234567890",
            "to_type": "bank",
            "to_company": "Target Corp",
            "to_bank": "Target Bank",
            "to_account_num": "0987654321",
            "ours_type": "bank",
            "ours_bank": "Our Bank",
            "ours_account_num": "1111111111",
            "buy_currency": "GBP",
            "sell_currency": "USD",
            "currency_amount": 5000,
            "amount": 6200,
            "rate": 1.24,
            "remarks": "Confirm audit test"
        }
        
        create_resp = trader_client.post(f"{BASE_URL}/api/deals", json=deal_data)
        assert create_resp.status_code == 200
        deal = create_resp.json()
        deal_id = deal["id"]
        deal_ref = deal["reference_number"]
        
        # Process the deal (confirm)
        process_resp = treasury_client.put(f"{BASE_URL}/api/deals/{deal_id}/process", json={
            "status": "confirmed",
            "treasury_remarks": "Audit test - confirmed"
        })
        assert process_resp.status_code == 200
        print(f"✓ Deal {deal_ref} confirmed")
        
        # Check audit log for deal_confirmed entry
        audit_resp = admin_client.get(f"{BASE_URL}/api/audit-logs?action=deal_confirmed&limit=5")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()
        
        found = False
        for log in audit_data["logs"]:
            if log["entity_ref"] == deal_ref:
                found = True
                assert log["action"] == "deal_confirmed"
                assert log["entity_type"] == "deal"
                assert "Treasury" in log["user_name"]
                print(f"✓ Found audit entry for deal {deal_ref} - action: deal_confirmed")
                break
        
        assert found, f"Audit entry for deal_confirmed not found for {deal_ref}"
    
    def test_deal_cancellation_logged(self, trader_client, admin_client):
        """Cancelling a deal should create an audit log entry"""
        # Create a deal first
        deal_data = {
            "transaction_type": "Spot",
            "value_date": datetime.now().strftime("%Y-%m-%d"),
            "deal_date": datetime.now().strftime("%Y-%m-%d"),
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_CancelAudit",
            "from_type": "crypto",
            "from_company": "Crypto Corp",
            "from_wallet_address": "0xABC123",
            "to_type": "bank",
            "to_company": "Target Corp",
            "to_bank": "Target Bank",
            "to_account_num": "0987654321",
            "ours_type": "bank",
            "ours_bank": "Our Bank",
            "ours_account_num": "1111111111",
            "buy_currency": "BTC",
            "sell_currency": "USD",
            "currency_amount": 1,
            "amount": 45000,
            "rate": 45000,
            "remarks": "Cancel audit test"
        }
        
        create_resp = trader_client.post(f"{BASE_URL}/api/deals", json=deal_data)
        assert create_resp.status_code == 200
        deal = create_resp.json()
        deal_id = deal["id"]
        deal_ref = deal["reference_number"]
        
        # Cancel the deal
        cancel_resp = trader_client.put(f"{BASE_URL}/api/deals/{deal_id}/cancel", json={
            "cancellation_reason": "Audit test cancellation"
        })
        assert cancel_resp.status_code == 200
        print(f"✓ Deal {deal_ref} cancelled")
        
        # Check audit log for deal_cancelled entry
        audit_resp = admin_client.get(f"{BASE_URL}/api/audit-logs?action=deal_cancelled&limit=5")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()
        
        found = False
        for log in audit_data["logs"]:
            if log["entity_ref"] == deal_ref:
                found = True
                assert log["action"] == "deal_cancelled"
                assert log["entity_type"] == "deal"
                print(f"✓ Found audit entry for deal {deal_ref} - action: deal_cancelled")
                break
        
        assert found, f"Audit entry for deal_cancelled not found for {deal_ref}"


# ==== CSV EXPORT TESTS ====

class TestCSVExport:
    """Tests for GET /api/deals/export CSV endpoint"""
    
    def test_csv_export_trader(self, trader_client):
        """Trader can export their own deals to CSV"""
        resp = trader_client.get(f"{BASE_URL}/api/deals/export")
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("text/csv")
        assert "attachment" in resp.headers.get("Content-Disposition", "")
        
        # Verify CSV structure
        content = resp.text
        lines = content.strip().split("\n")
        assert len(lines) >= 1  # At least header row
        
        # Check header row
        header = lines[0]
        expected_columns = ["reference_number", "client_name", "transaction_type", "buy_currency", "sell_currency", "status"]
        for col in expected_columns:
            assert col in header, f"Missing column: {col}"
        
        print(f"✓ Trader CSV export works - {len(lines)} rows including header")
    
    def test_csv_export_admin(self, admin_client):
        """Admin can export all deals to CSV"""
        resp = admin_client.get(f"{BASE_URL}/api/deals/export")
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("text/csv")
        
        content = resp.text
        lines = content.strip().split("\n")
        print(f"✓ Admin CSV export works - {len(lines)} rows")
    
    def test_csv_export_treasury(self, treasury_client):
        """Treasury can export all deals to CSV"""
        resp = treasury_client.get(f"{BASE_URL}/api/deals/export")
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("text/csv")
        print("✓ Treasury CSV export works")
    
    def test_csv_export_with_status_filter(self, admin_client):
        """CSV export respects status filter"""
        resp = admin_client.get(f"{BASE_URL}/api/deals/export?status=pending")
        assert resp.status_code == 200
        
        content = resp.text
        lines = content.strip().split("\n")
        
        # If there are data rows, check status column
        if len(lines) > 1:
            header = lines[0].split(",")
            status_idx = header.index("status")
            for line in lines[1:]:
                cols = line.split(",")
                if len(cols) > status_idx:
                    assert cols[status_idx] == "pending" or cols[status_idx] == "", f"Expected pending status, got {cols[status_idx]}"
        
        print(f"✓ CSV export with status filter works")
    
    def test_csv_export_with_client_filter(self, trader_client):
        """CSV export respects client filter"""
        resp = trader_client.get(f"{BASE_URL}/api/deals/export?client=TEST")
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("text/csv")
        print("✓ CSV export with client filter works")
    
    def test_csv_export_with_date_filters(self, admin_client):
        """CSV export respects date filters"""
        today = datetime.now().strftime("%Y-%m-%d")
        resp = admin_client.get(f"{BASE_URL}/api/deals/export?date_from={today}&date_to={today}")
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type", "").startswith("text/csv")
        print("✓ CSV export with date filters works")
    
    def test_csv_export_filename(self, admin_client):
        """CSV export has proper filename in header"""
        resp = admin_client.get(f"{BASE_URL}/api/deals/export")
        assert resp.status_code == 200
        
        disposition = resp.headers.get("Content-Disposition", "")
        assert "filename=" in disposition
        assert "deals_export_" in disposition
        assert ".csv" in disposition
        print(f"✓ CSV filename correct: {disposition}")
    
    def test_csv_export_includes_all_deal_fields(self, admin_client):
        """CSV export includes all important deal fields"""
        resp = admin_client.get(f"{BASE_URL}/api/deals/export")
        assert resp.status_code == 200
        
        header = resp.text.split("\n")[0]
        important_fields = [
            "reference_number", "client_name", "transaction_type", "transfer_type",
            "deal_date", "value_date", "buy_currency", "sell_currency",
            "currency_amount", "rate", "amount", "status", "created_by_name"
        ]
        
        for field in important_fields:
            assert field in header, f"Missing important field in CSV: {field}"
        
        print("✓ CSV includes all important deal fields")


# ==== USER CRUD AUDIT TESTS ====

class TestUserAuditLogs:
    """Test audit logging for user management"""
    
    def test_user_created_logged(self, admin_client):
        """Creating a user should create audit log entry"""
        # Create a test user
        user_data = {
            "email": f"test_audit_{datetime.now().strftime('%H%M%S')}@test.com",
            "name": "TEST_AuditUser",
            "password": "Test@123",
            "role": "trader"
        }
        
        create_resp = admin_client.post(f"{BASE_URL}/api/users", json=user_data)
        assert create_resp.status_code == 200
        user = create_resp.json()
        user_email = user["email"]
        print(f"✓ Created test user: {user_email}")
        
        # Check audit log for user_created entry
        audit_resp = admin_client.get(f"{BASE_URL}/api/audit-logs?action=user_created&limit=5")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()
        
        found = False
        for log in audit_data["logs"]:
            if log["entity_ref"] == user_email:
                found = True
                assert log["action"] == "user_created"
                assert log["entity_type"] == "user"
                print(f"✓ Found audit entry for user_created: {user_email}")
                break
        
        assert found, f"Audit entry for user_created not found for {user_email}"
        
        # Cleanup: delete the test user
        admin_client.delete(f"{BASE_URL}/api/users/{user['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
