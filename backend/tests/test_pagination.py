"""
Test server-side pagination for FX Trading Tracker
Tests GET /api/deals and GET /api/users pagination functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TRADER_EMAIL = "trader@fxtracker.com"
TRADER_PASS = "Trader@123"
ADMIN_EMAIL = "admin@fxtracker.com"
ADMIN_PASS = "Admin@123"
TREASURY_EMAIL = "treasury@fxtracker.com"
TREASURY_PASS = "Treasury@123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def trader_token(api_client):
    """Get trader authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TRADER_EMAIL,
        "password": TRADER_PASS
    })
    assert response.status_code == 200, f"Trader login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASS
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def treasury_token(api_client):
    """Get treasury authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TREASURY_EMAIL,
        "password": TREASURY_PASS
    })
    assert response.status_code == 200, f"Treasury login failed: {response.text}"
    return response.json().get("token")


class TestDealsAPIPagination:
    """Test GET /api/deals pagination functionality"""
    
    def test_deals_returns_paginated_format(self, api_client, trader_token):
        """Test that /api/deals returns proper pagination structure {deals, total, page, pages}"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "deals" in data, "Response should contain 'deals' key"
        assert "total" in data, "Response should contain 'total' key"
        assert "page" in data, "Response should contain 'page' key"
        assert "pages" in data, "Response should contain 'pages' key"
        
        # Verify types
        assert isinstance(data["deals"], list), "'deals' should be a list"
        assert isinstance(data["total"], int), "'total' should be an integer"
        assert isinstance(data["page"], int), "'page' should be an integer"
        assert isinstance(data["pages"], int), "'pages' should be an integer"
        
        # Verify pagination values
        assert data["page"] == 1, "Page should be 1"
        assert len(data["deals"]) <= 5, "Should not exceed limit of 5"
        print(f"Deals pagination test passed: {data['total']} total, page {data['page']} of {data['pages']}")
    
    def test_deals_page_2_returns_different_data(self, api_client, admin_token):
        """Test that page 2 returns different deals than page 1 (admin sees all deals)"""
        # Get page 1
        response1 = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        if data1["pages"] < 2:
            pytest.skip("Not enough deals for multiple pages")
        
        # Get page 2
        response2 = api_client.get(
            f"{BASE_URL}/api/deals?page=2&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify different data
        ids_page1 = {d["id"] for d in data1["deals"]}
        ids_page2 = {d["id"] for d in data2["deals"]}
        
        assert ids_page1.isdisjoint(ids_page2), "Page 1 and Page 2 should have different deals"
        assert data2["page"] == 2, "Page should be 2"
        print(f"Page 2 test passed: Page 1 IDs vs Page 2 IDs are different")
    
    def test_deals_limit_parameter_works(self, api_client, trader_token):
        """Test that limit parameter controls number of results"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=3",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are at least 3 deals, should return exactly 3
        if data["total"] >= 3:
            assert len(data["deals"]) == 3, f"Should return 3 deals, got {len(data['deals'])}"
        else:
            assert len(data["deals"]) == data["total"], "Should return all available deals"
        print(f"Limit test passed: {len(data['deals'])} deals returned with limit=3")
    
    def test_deals_pagination_with_status_filter(self, api_client, trader_token):
        """Test pagination works with status filter"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5&status=pending",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "deals" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        # Verify all returned deals are pending
        for deal in data["deals"]:
            assert deal["status"] == "pending", f"Deal {deal['id']} should be pending"
        print(f"Status filter + pagination test passed: {data['total']} pending deals total")
    
    def test_deals_pagination_with_multiple_filters(self, api_client, trader_token):
        """Test pagination works with combined filters"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5&status=pending&currency=USD",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure exists
        assert "deals" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        print(f"Multiple filters + pagination test passed: {data['total']} matching deals")
    
    def test_deals_pages_calculation_correct(self, api_client, trader_token):
        """Test that pages calculation is correct (total / limit, rounded up)"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        expected_pages = (data["total"] + 4) // 5 if data["total"] > 0 else 1
        assert data["pages"] == expected_pages, f"Expected {expected_pages} pages, got {data['pages']}"
        print(f"Pages calculation test passed: {data['total']} total / 5 limit = {data['pages']} pages")


class TestUsersAPIPagination:
    """Test GET /api/users pagination functionality (Admin only)"""
    
    def test_users_returns_paginated_format(self, api_client, admin_token):
        """Test that /api/users returns proper pagination structure {users, total, page, pages}"""
        response = api_client.get(
            f"{BASE_URL}/api/users?page=1&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "users" in data, "Response should contain 'users' key"
        assert "total" in data, "Response should contain 'total' key"
        assert "page" in data, "Response should contain 'page' key"
        assert "pages" in data, "Response should contain 'pages' key"
        
        # Verify types
        assert isinstance(data["users"], list), "'users' should be a list"
        assert isinstance(data["total"], int), "'total' should be an integer"
        assert isinstance(data["page"], int), "'page' should be an integer"
        assert isinstance(data["pages"], int), "'pages' should be an integer"
        
        assert data["page"] == 1, "Page should be 1"
        print(f"Users pagination test passed: {data['total']} total users, page {data['page']} of {data['pages']}")
    
    def test_users_search_parameter_works(self, api_client, admin_token):
        """Test that search parameter filters users"""
        response = api_client.get(
            f"{BASE_URL}/api/users?page=1&limit=5&search=trader",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "users" in data
        assert "total" in data
        
        # If any results, verify search worked (name or email contains "trader")
        for user in data["users"]:
            name_match = "trader" in user.get("name", "").lower()
            email_match = "trader" in user.get("email", "").lower()
            assert name_match or email_match, f"User {user['id']} doesn't match search 'trader'"
        print(f"Users search test passed: {data['total']} users matching 'trader'")
    
    def test_users_endpoint_requires_admin(self, api_client, trader_token):
        """Test that non-admin users cannot access /api/users"""
        response = api_client.get(
            f"{BASE_URL}/api/users?page=1&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 403, "Non-admin should get 403 Forbidden"
        print("Users admin-only access test passed")
    
    def test_users_search_with_pagination(self, api_client, admin_token):
        """Test search combined with pagination"""
        response = api_client.get(
            f"{BASE_URL}/api/users?page=1&limit=2&search=admin",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert len(data["users"]) <= 2, "Should respect limit"
        print(f"Users search + pagination test passed: {data['total']} users matching 'admin'")


class TestDealsExportNotPaginated:
    """Test that /api/deals/export returns ALL matching records, not paginated"""
    
    def test_export_returns_all_records(self, api_client, trader_token):
        """Test CSV export returns all records regardless of pagination"""
        # First check how many deals the trader has
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        total_deals = data["total"]
        
        if total_deals == 0:
            pytest.skip("No deals to export")
        
        # Now export CSV
        export_response = api_client.get(
            f"{BASE_URL}/api/deals/export",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert export_response.status_code == 200
        assert "text/csv" in export_response.headers.get("Content-Type", "")
        
        # Count CSV rows (minus header)
        csv_content = export_response.text
        csv_lines = csv_content.strip().split("\n")
        csv_rows = len(csv_lines) - 1  # Subtract header
        
        # CSV should have all deals, not just first page
        assert csv_rows == total_deals, f"CSV should have {total_deals} rows, got {csv_rows}"
        print(f"CSV export test passed: {csv_rows} rows exported (all {total_deals} deals)")
    
    def test_export_with_filter_returns_all_matching(self, api_client, trader_token):
        """Test CSV export with filter returns all matching records"""
        # First check filtered count
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5&status=pending",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        pending_total = data["total"]
        
        if pending_total == 0:
            pytest.skip("No pending deals to export")
        
        # Export with filter
        export_response = api_client.get(
            f"{BASE_URL}/api/deals/export?status=pending",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert export_response.status_code == 200
        
        csv_content = export_response.text
        csv_lines = csv_content.strip().split("\n")
        csv_rows = len(csv_lines) - 1
        
        # Should export all pending, not just first page
        assert csv_rows == pending_total, f"CSV should have {pending_total} pending deals, got {csv_rows}"
        print(f"Filtered CSV export test passed: {csv_rows} pending deals exported")


class TestTreasuryPagination:
    """Test Treasury role pagination - sees all deals but paginated"""
    
    def test_treasury_sees_paginated_deals(self, api_client, treasury_token):
        """Test treasury user gets paginated deal list"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {treasury_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "deals" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        # Treasury should see all deals (not filtered by created_by)
        print(f"Treasury pagination test passed: {data['total']} total deals visible")


class TestEdgeCases:
    """Test edge cases for pagination"""
    
    def test_page_beyond_max_returns_empty(self, api_client, trader_token):
        """Test requesting page beyond max returns empty deals list"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        data = response.json()
        max_page = data["pages"]
        
        # Request page beyond max
        response2 = api_client.get(
            f"{BASE_URL}/api/deals?page={max_page + 10}&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert len(data2["deals"]) == 0, "Page beyond max should return empty deals"
        print(f"Beyond max page test passed: page {max_page + 10} returns empty")
    
    def test_default_limit_is_20(self, api_client, trader_token):
        """Test that default limit is 20 when not specified"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=1",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If more than 20 deals exist, should return exactly 20
        if data["total"] > 20:
            assert len(data["deals"]) == 20, f"Default limit should be 20, got {len(data['deals'])}"
        print(f"Default limit test passed: returned {len(data['deals'])} deals")
    
    def test_invalid_page_number(self, api_client, trader_token):
        """Test that page=0 or negative is handled"""
        response = api_client.get(
            f"{BASE_URL}/api/deals?page=0&limit=5",
            headers={"Authorization": f"Bearer {trader_token}"}
        )
        # Should either return 422 (validation error) or treat as page 1
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        print(f"Invalid page test: page=0 returns status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
