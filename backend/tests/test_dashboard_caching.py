"""
Test Dashboard Statistics API
Validates the /api/dashboard/stats endpoint across different roles and date ranges.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    "trader": {"email": "trader@fxtracker.com", "password": "Trader@123"},
    "treasury": {"email": "treasury@fxtracker.com", "password": "Treasury@123"},
    "admin": {"email": "admin@fxtracker.com", "password": "Admin@123"}
}

def get_auth_token(role):
    """Helper to get auth token for a specific role"""
    creds = CREDENTIALS[role]
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": creds["email"], "password": creds["password"]}
    )
    if response.status_code != 200:
        pytest.skip(f"Failed to authenticate as {role}")
    return response.json()["token"]


class TestDashboardStatsAPI:
    """Tests for GET /api/dashboard/stats endpoint"""
    
    def test_dashboard_stats_default_range(self):
        """Test dashboard stats with default 30d range"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deals" in data
        assert "pending_deals" in data
        assert "confirmed_deals" in data
        assert "returned_deals" in data
        assert "total_volume" in data
        assert "deals_by_date" in data
        assert "recent_deals" in data
        
        # Validate data types
        assert isinstance(data["total_deals"], int)
        assert isinstance(data["pending_deals"], int)
        assert isinstance(data["total_volume"], (int, float))
        assert isinstance(data["deals_by_date"], list)
        assert isinstance(data["recent_deals"], list)
    
    def test_dashboard_stats_7d_range(self):
        """Test dashboard stats with 7d range"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=7d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deals" in data
        assert isinstance(data["total_deals"], int)
    
    def test_dashboard_stats_ytd_range(self):
        """Test dashboard stats with YTD range"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=ytd",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deals" in data
    
    def test_dashboard_stats_all_time_range(self):
        """Test dashboard stats with all time range"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=all",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_deals" in data
    
    def test_dashboard_stats_requires_auth(self):
        """Test that dashboard stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403]
    
    def test_admin_sees_total_users(self):
        """Test that admin role gets total_users in response"""
        token = get_auth_token("admin")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data, "Admin should see total_users metric"
        assert isinstance(data["total_users"], int)
        assert data["total_users"] >= 3  # At least 3 seed users
    
    def test_trader_no_total_users(self):
        """Test that trader role does NOT get total_users in response"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" not in data, "Trader should NOT see total_users metric"
    
    def test_treasury_no_total_users(self):
        """Test that treasury role does NOT get total_users in response"""
        token = get_auth_token("treasury")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" not in data, "Treasury should NOT see total_users metric"
    
    def test_recent_deals_structure(self):
        """Test that recent_deals have correct structure"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        recent_deals = data.get("recent_deals", [])
        
        if len(recent_deals) > 0:
            deal = recent_deals[0]
            # Check deal structure
            assert "reference_number" in deal
            assert "status" in deal
            assert "amount" in deal
            assert "buy_currency" in deal
            assert "sell_currency" in deal
    
    def test_deals_by_date_structure(self):
        """Test that deals_by_date has correct structure"""
        token = get_auth_token("trader")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=30d",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        deals_by_date = data.get("deals_by_date", [])
        
        if len(deals_by_date) > 0:
            entry = deals_by_date[0]
            assert "date" in entry
            assert "count" in entry
            assert isinstance(entry["count"], int)


class TestDashboardStatsConsistency:
    """Tests for data consistency in dashboard stats"""
    
    def test_status_counts_add_up(self):
        """Test that status counts add up to total deals"""
        token = get_auth_token("admin")
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats?range=all",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        total = data["total_deals"]
        pending = data["pending_deals"]
        confirmed = data["confirmed_deals"]
        returned = data["returned_deals"]
        cancelled = data.get("cancelled_deals", 0)
        
        # Sum of statuses should equal or be close to total
        status_sum = pending + confirmed + returned + cancelled
        assert status_sum == total, f"Status counts ({status_sum}) don't match total ({total})"
    
    def test_multiple_requests_same_data(self):
        """Test that multiple rapid requests return consistent data"""
        token = get_auth_token("trader")
        
        results = []
        for _ in range(3):
            response = requests.get(
                f"{BASE_URL}/api/dashboard/stats?range=30d",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            results.append(response.json()["total_deals"])
        
        # All requests should return same total
        assert len(set(results)) == 1, "Multiple requests returned different totals"
