"""
Test suite for NewDealPage performance optimization verification
Tests API endpoints for deal creation, reference data, and data integrity
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture
def api_client():
    """Create a requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def trader_token(api_client):
    """Get trader authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "trader@fxtracker.com",
        "password": "Trader@123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Trader authentication failed")

@pytest.fixture
def authenticated_client(api_client, trader_token):
    """Session with trader auth header"""
    api_client.headers.update({"Authorization": f"Bearer {trader_token}"})
    return api_client


class TestReferenceDataEndpoints:
    """Reference data endpoints used by NewDealPage"""
    
    def test_companies_endpoint(self, authenticated_client):
        """Test /api/reference/companies endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/reference/companies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "code" in data[0]
            assert "is_active" in data[0]
        print(f"✓ Companies: {len(data)} items returned")
    
    def test_banks_endpoint(self, authenticated_client):
        """Test /api/reference/banks endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/reference/banks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Banks: {len(data)} items returned")
    
    def test_transaction_types_endpoint(self, authenticated_client):
        """Test /api/reference/transaction-types endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/reference/transaction-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Transaction Types: {len(data)} items returned")
    
    def test_transfer_types_endpoint(self, authenticated_client):
        """Test /api/reference/transfer-types endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/reference/transfer-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Transfer Types: {len(data)} items returned")
    
    def test_currencies_endpoint(self, authenticated_client):
        """Test /api/reference/currencies endpoint - should have fiat, stablecoin, crypto types"""
        response = authenticated_client.get(f"{BASE_URL}/api/reference/currencies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check for different currency types
        types_found = set(c.get("type") for c in data)
        print(f"✓ Currencies: {len(data)} items, types: {types_found}")
        
        # Verify currency structure
        if len(data) > 0:
            assert "code" in data[0]
            assert "name" in data[0]
            assert "type" in data[0]


class TestDealCreation:
    """Deal creation and retrieval tests"""
    
    def test_create_deal_with_all_fields(self, authenticated_client):
        """Test creating a deal with all required fields"""
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Performance_API_Client",
            "deal_date": "2026-03-13",
            "value_date": "2026-03-13",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "API123456",
            "from_wallet_address": "",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "HSBC",
            "to_account_num": "API654321",
            "to_wallet_address": "",
            "ours_type": "bank",
            "ours_bank": "Citibank",
            "ours_account_num": "APIOURS789",
            "ours_wallet_address": "",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 25000,
            "amount": 22750,  # 25000 * 0.91
            "rate": 0.91,
            "remarks": "API test deal for performance verification"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/deals", json=deal_data)
        assert response.status_code in [200, 201], f"Failed to create deal: {response.text}"
        
        created_deal = response.json()
        assert created_deal.get("client_name") == deal_data["client_name"]
        assert created_deal.get("buy_currency") == "USD"
        assert created_deal.get("sell_currency") == "EUR"
        assert "id" in created_deal or "reference" in created_deal
        print(f"✓ Deal created successfully: {created_deal.get('reference', created_deal.get('id'))}")
        
        return created_deal
    
    def test_get_deals_list(self, authenticated_client):
        """Test retrieving deals list"""
        response = authenticated_client.get(f"{BASE_URL}/api/deals")
        assert response.status_code == 200
        data = response.json()
        
        # Check if it's paginated or a list
        if isinstance(data, dict) and "deals" in data:
            deals = data["deals"]
            total = data.get("total", len(deals))
        elif isinstance(data, dict) and "items" in data:
            deals = data["items"]
            total = data.get("total", len(deals))
        else:
            deals = data
            total = len(deals)
        
        assert isinstance(deals, list)
        print(f"✓ Deals list: {len(deals)} deals returned (total: {total})")
        
        # Verify deal structure
        if len(deals) > 0:
            deal = deals[0]
            assert "client_name" in deal
            assert "buy_currency" in deal or "currency_amount" in deal


class TestDealCreationWithCrypto:
    """Test deal creation with crypto wallet fields"""
    
    def test_create_deal_with_crypto_from(self, authenticated_client):
        """Test creating a deal with crypto source"""
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Crypto_Source_Client",
            "deal_date": "2026-03-13",
            "value_date": "2026-03-14",
            "from_type": "crypto",
            "from_company": "Pacific Trading Co",
            "from_bank": "",
            "from_account_num": "",
            "from_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "to_type": "bank",
            "to_company": "Sterling Enterprises",
            "to_bank": "Deutsche Bank",
            "to_account_num": "DE789012345",
            "to_wallet_address": "",
            "ours_type": "crypto",
            "ours_bank": "",
            "ours_account_num": "",
            "ours_wallet_address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "buy_currency": "BTC",
            "sell_currency": "USD",
            "currency_amount": 1.5,
            "amount": 67500,  # 1.5 BTC * 45000 USD
            "rate": 45000,
            "remarks": "Crypto test deal"
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/deals", json=deal_data)
        assert response.status_code in [200, 201], f"Failed to create crypto deal: {response.text}"
        
        created_deal = response.json()
        assert created_deal.get("from_type") == "crypto"
        assert created_deal.get("from_wallet_address") == deal_data["from_wallet_address"]
        print(f"✓ Crypto deal created: {created_deal.get('reference', created_deal.get('id'))}")


class TestAPIPerformance:
    """API response time tests"""
    
    def test_reference_data_response_times(self, authenticated_client):
        """Test that reference data endpoints respond quickly"""
        endpoints = [
            "/api/reference/companies",
            "/api/reference/banks",
            "/api/reference/transaction-types",
            "/api/reference/transfer-types",
            "/api/reference/currencies"
        ]
        
        for endpoint in endpoints:
            start = time.time()
            response = authenticated_client.get(f"{BASE_URL}{endpoint}")
            duration = time.time() - start
            
            assert response.status_code == 200
            assert duration < 2.0, f"{endpoint} took {duration:.2f}s (should be <2s)"
            print(f"✓ {endpoint}: {duration*1000:.0f}ms")
    
    def test_deals_list_response_time(self, authenticated_client):
        """Test deals list endpoint performance"""
        start = time.time()
        response = authenticated_client.get(f"{BASE_URL}/api/deals")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Deals list took {duration:.2f}s"
        print(f"✓ /api/deals: {duration*1000:.0f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
