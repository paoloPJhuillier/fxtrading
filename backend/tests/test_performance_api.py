"""
Performance and Dashboard API Tests for FX Trading Tracker
Tests dashboard aggregation pipeline and API response times
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthPerformance:
    """Authentication API performance tests"""
    
    def test_login_trader_response_time(self):
        """Login should respond quickly"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Login took {elapsed:.2f}s, should be < 2s"
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "trader"
    
    def test_login_admin_response_time(self):
        """Admin login should respond quickly"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0
        
        data = response.json()
        assert data["user"]["role"] == "admin"
    
    def test_login_treasury_response_time(self):
        """Treasury login should respond quickly"""
        start = time.time()
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "treasury@fxtracker.com",
            "password": "Treasury@123"
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0
        
        data = response.json()
        assert data["user"]["role"] == "treasury"


class TestDashboardAggregation:
    """Dashboard stats API tests - verifies MongoDB aggregation pipeline"""
    
    @pytest.fixture(autouse=True)
    def setup_tokens(self):
        """Get auth tokens for all roles"""
        # Trader token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        self.trader_token = response.json()["token"]
        
        # Admin token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        self.admin_token = response.json()["token"]
        
        # Treasury token
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "treasury@fxtracker.com",
            "password": "Treasury@123"
        })
        self.treasury_token = response.json()["token"]
    
    def test_dashboard_stats_7d_performance(self):
        """Dashboard 7d stats should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=7d",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Dashboard stats took {elapsed:.2f}s, should be < 0.5s"
        
        data = response.json()
        # Verify structure
        assert "total_deals" in data
        assert "pending_deals" in data
        assert "confirmed_deals" in data
        assert "returned_deals" in data
        assert "total_volume" in data
        assert "deals_by_date" in data
        assert "recent_deals" in data
    
    def test_dashboard_stats_30d_performance(self):
        """Dashboard 30d stats should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
    
    def test_dashboard_stats_ytd_performance(self):
        """Dashboard YTD stats should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=ytd",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
    
    def test_dashboard_stats_all_time(self):
        """Dashboard all-time stats should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=all",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
    
    def test_dashboard_stats_data_integrity(self):
        """Verify dashboard stats data is correct and complete"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=all",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify counts match
        total = data["total_deals"]
        pending = data["pending_deals"]
        confirmed = data["confirmed_deals"]
        returned = data["returned_deals"]
        cancelled = data.get("cancelled_deals", 0)
        
        # Total should equal sum of all statuses
        assert total == pending + confirmed + returned + cancelled, \
            f"Total {total} != sum of statuses {pending + confirmed + returned + cancelled}"
        
        # recent_deals should have max 10 entries
        assert len(data["recent_deals"]) <= 10
        
        # Each recent deal should have required fields
        if data["recent_deals"]:
            deal = data["recent_deals"][0]
            assert "id" in deal
            assert "reference_number" in deal
            assert "status" in deal
            assert "client_name" in deal
    
    def test_admin_gets_total_users(self):
        """Admin should see total_users in dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert data["total_users"] >= 3  # At least 3 default users
    
    def test_trader_does_not_see_total_users(self):
        """Trader should NOT see total_users in dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {self.trader_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" not in data
    
    def test_treasury_does_not_see_total_users(self):
        """Treasury should NOT see total_users in dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {self.treasury_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" not in data


class TestDealsAPIPerformance:
    """Deals API performance tests"""
    
    @pytest.fixture(autouse=True)
    def setup_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        self.token = response.json()["token"]
    
    def test_deals_list_performance(self):
        """Deals list should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/deals?page=1&limit=20",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
        
        data = response.json()
        assert "deals" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
    
    def test_deals_list_with_filters(self):
        """Deals list with filters should respond quickly"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/deals?page=1&limit=20&status=pending",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5


class TestUsersAPIPerformance:
    """Users API performance tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
    
    def test_users_list_performance(self):
        """Users list should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/users?page=1&limit=20",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["total"] >= 3


class TestAuditLogAPIPerformance:
    """Audit log API performance tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        self.token = response.json()["token"]
    
    def test_audit_logs_performance(self):
        """Audit logs should respond in <500ms"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/audit-logs?page=1&limit=50",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5
        
        data = response.json()
        assert "logs" in data
        assert "total" in data


class TestCSVExportPerformance:
    """CSV export API tests"""
    
    @pytest.fixture(autouse=True)
    def setup_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        self.token = response.json()["token"]
    
    def test_csv_export_returns_csv(self):
        """CSV export should return proper CSV"""
        response = requests.get(
            f"{BASE_URL}/api/deals/export",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        # Check CSV has header row
        content = response.text
        assert "reference_number" in content
        assert "client_name" in content
