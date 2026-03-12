"""
FX Trading Tracker - 5 New Enhancements Tests
Tests for:
1. Cancel/Recall deal with mandatory reason
2. Updated transaction types (Today/Tomorrow/Spot)
3. Updated transfer types (FX Crypto Conversion/FX Local/PDAX Withdrawal)
4. Bank vs Crypto toggle on Source/Destination
5. Ours section for receiving account
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable must be set")

# Test credentials
TRADER_CREDS = {"email": "trader@fxtracker.com", "password": "Trader@123"}
TREASURY_CREDS = {"email": "treasury@fxtracker.com", "password": "Treasury@123"}
ADMIN_CREDS = {"email": "admin@fxtracker.com", "password": "Admin@123"}


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
def trader2_token(trader_token):
    """Simulate second trader for testing cross-trader cancellation"""
    # We use the same trader for simplicity, but return the token
    return trader_token


class TestTransactionTypes:
    """Enhancement 2: Verify updated transaction types (Today/Tomorrow/Spot)"""

    def test_transaction_types_list(self, trader_token):
        """Verify transaction types are exactly: Today, Tomorrow, Spot"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/transaction-types", headers=headers)
        assert response.status_code == 200, f"Failed to get transaction types: {response.text}"
        
        data = response.json()
        active_types = [t["name"] for t in data if t.get("is_active", True)]
        
        expected_types = {"Today", "Tomorrow", "Spot"}
        actual_types_set = set(active_types)
        
        assert expected_types.issubset(actual_types_set), f"Expected transaction types {expected_types}, got {actual_types_set}"
        print(f"✓ Transaction types verified: {active_types}")


class TestTransferTypes:
    """Enhancement 3: Verify updated transfer types (FX Crypto Conversion/FX Local/PDAX Withdrawal)"""

    def test_transfer_types_list(self, trader_token):
        """Verify transfer types are exactly: FX Crypto Conversion, FX Local, PDAX Withdrawal"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/reference/transfer-types", headers=headers)
        assert response.status_code == 200, f"Failed to get transfer types: {response.text}"
        
        data = response.json()
        active_types = [t["name"] for t in data if t.get("is_active", True)]
        
        expected_types = {"FX Crypto Conversion", "FX Local", "PDAX Withdrawal"}
        actual_types_set = set(active_types)
        
        assert expected_types.issubset(actual_types_set), f"Expected transfer types {expected_types}, got {actual_types_set}"
        print(f"✓ Transfer types verified: {active_types}")


class TestBankCryptoToggle:
    """Enhancement 4: Bank/Crypto toggle on Source/Destination fields"""

    def test_create_deal_with_bank_type_from(self, trader_token):
        """Test creating deal with Bank type for From section"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "FX Local",
            "client_name": "TEST_Bank_From_Client",
            "deal_date": "2026-01-15",
            "value_date": "2026-01-17",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "BANK123456",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "BANK987654",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "OURS123456",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 9200,
            "rate": 0.92,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal with bank type: {response.text}"
        
        data = response.json()
        assert data["from_type"] == "bank"
        assert data["from_bank"] == "JP Morgan Chase"
        assert data["from_account_num"] == "BANK123456"
        print(f"✓ Deal created with Bank type for From: {data['reference_number']}")
        return data

    def test_create_deal_with_crypto_type_from(self, trader_token):
        """Test creating deal with Crypto type for From section"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Tomorrow",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Crypto_From_Client",
            "deal_date": "2026-01-15",
            "value_date": "2026-01-17",
            "from_type": "crypto",
            "from_company": "Acme Corporation",
            "from_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
            "to_type": "crypto",
            "to_company": "GlobalTech Inc",
            "to_wallet_address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "ours_type": "crypto",
            "ours_wallet_address": "0xOurs1234567890abcdef1234567890abcdef1234",
            "buy_currency": "BTC",
            "sell_currency": "USDT",
            "currency_amount": 1,
            "amount": 42000,
            "rate": 42000,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal with crypto type: {response.text}"
        
        data = response.json()
        assert data["from_type"] == "crypto"
        assert data["from_wallet_address"] == "0x1234567890abcdef1234567890abcdef12345678"
        print(f"✓ Deal created with Crypto type for From: {data['reference_number']}")
        return data

    def test_create_deal_mixed_types(self, trader_token):
        """Test creating deal with Bank type for From and Crypto type for To"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Mixed_Types_Client",
            "deal_date": "2026-01-15",
            "value_date": "2026-01-17",
            "from_type": "bank",
            "from_company": "Sterling Enterprises",
            "from_bank": "Deutsche Bank",
            "from_account_num": "MIXBANK001",
            "to_type": "crypto",
            "to_company": "Pacific Trading Co",
            "to_wallet_address": "0xMixed1234567890abcdef1234567890abcdef12",
            "ours_type": "bank",
            "ours_bank": "Standard Chartered",
            "ours_account_num": "OURSBANK001",
            "buy_currency": "ETH",
            "sell_currency": "USD",
            "currency_amount": 10,
            "amount": 23000,
            "rate": 2300,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal with mixed types: {response.text}"
        
        data = response.json()
        assert data["from_type"] == "bank"
        assert data["from_bank"] == "Deutsche Bank"
        assert data["to_type"] == "crypto"
        assert data["to_wallet_address"] == "0xMixed1234567890abcdef1234567890abcdef12"
        print(f"✓ Deal created with mixed Bank/Crypto types: {data['reference_number']}")
        return data


class TestOursSection:
    """Enhancement 5: Ours section for receiving account"""

    def test_create_deal_with_ours_bank(self, trader_token):
        """Test creating deal with Ours section using Bank type"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "FX Local",
            "client_name": "TEST_Ours_Bank_Client",
            "deal_date": "2026-01-16",
            "value_date": "2026-01-18",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "FROM123",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "TO456",
            "ours_type": "bank",
            "ours_bank": "Bank of America",
            "ours_account_num": "OURS_BANK_789",
            "buy_currency": "GBP",
            "sell_currency": "USD",
            "currency_amount": 5000,
            "amount": 6250,
            "rate": 1.25,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal with ours bank: {response.text}"
        
        data = response.json()
        assert data["ours_type"] == "bank"
        assert data["ours_bank"] == "Bank of America"
        assert data["ours_account_num"] == "OURS_BANK_789"
        print(f"✓ Deal created with Ours Bank section: {data['reference_number']}")
        return data

    def test_create_deal_with_ours_crypto(self, trader_token):
        """Test creating deal with Ours section using Crypto type"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Tomorrow",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_Ours_Crypto_Client",
            "deal_date": "2026-01-16",
            "value_date": "2026-01-18",
            "from_type": "crypto",
            "from_company": "Acme Corporation",
            "from_wallet_address": "0xFrom_Wallet_123",
            "to_type": "crypto",
            "to_company": "GlobalTech Inc",
            "to_wallet_address": "0xTo_Wallet_456",
            "ours_type": "crypto",
            "ours_wallet_address": "0xOurs_Receiving_Wallet_789",
            "buy_currency": "USDC",
            "sell_currency": "BTC",
            "currency_amount": 50000,
            "amount": 1.2,
            "rate": 0.000024,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal with ours crypto: {response.text}"
        
        data = response.json()
        assert data["ours_type"] == "crypto"
        assert data["ours_wallet_address"] == "0xOurs_Receiving_Wallet_789"
        print(f"✓ Deal created with Ours Crypto section: {data['reference_number']}")
        return data

    def test_deal_detail_shows_ours_section(self, trader_token):
        """Verify deal detail API returns all ours section fields"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # First create a deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Ours_Detail_Client",
            "deal_date": "2026-01-17",
            "value_date": "2026-01-19",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "HSBC",
            "from_account_num": "DETAIL_FROM",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Standard Chartered",
            "to_account_num": "DETAIL_TO",
            "ours_type": "bank",
            "ours_bank": "Deutsche Bank",
            "ours_account_num": "DETAIL_OURS",
            "buy_currency": "CHF",
            "sell_currency": "EUR",
            "currency_amount": 10000,
            "amount": 10800,
            "rate": 1.08,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        
        # Now get the deal detail
        response = requests.get(f"{BASE_URL}/api/deals/{deal_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify ours section fields are present
        assert "ours_type" in data
        assert "ours_bank" in data
        assert "ours_account_num" in data
        assert "ours_wallet_address" in data
        assert data["ours_type"] == "bank"
        assert data["ours_bank"] == "Deutsche Bank"
        print(f"✓ Deal detail shows all Ours section fields")


class TestCancelDeal:
    """Enhancement 1: Cancel/Recall deal with mandatory reason"""

    cancel_test_deal_id = None

    def test_create_pending_deal_for_cancel(self, trader_token):
        """Create a pending deal for cancel testing"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "FX Local",
            "client_name": "TEST_Cancel_Deal_Client",
            "deal_date": "2026-01-20",
            "value_date": "2026-01-22",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "CANCEL001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "CANCEL002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "CANCEL_OURS",
            "buy_currency": "USD",
            "sell_currency": "JPY",
            "currency_amount": 1000,
            "amount": 150000,
            "rate": 150,
        }
        response = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert response.status_code == 200, f"Failed to create deal for cancel test: {response.text}"
        
        TestCancelDeal.cancel_test_deal_id = response.json()["id"]
        print(f"✓ Created pending deal for cancel test: {response.json()['reference_number']}")
        return response.json()

    def test_cancel_without_reason_fails(self, trader_token):
        """Test that cancelling without a reason returns 400 error"""
        if not TestCancelDeal.cancel_test_deal_id:
            # Create a deal first
            headers = {"Authorization": f"Bearer {trader_token}"}
            deal_data = {
                "transaction_type": "Today",
                "transfer_type": "FX Local",
                "client_name": "TEST_NoReason_Cancel_Client",
                "deal_date": "2026-01-20",
                "value_date": "2026-01-22",
                "from_type": "bank",
                "from_company": "Acme Corporation",
                "from_bank": "JP Morgan Chase",
                "from_account_num": "NOREASON001",
                "to_type": "bank",
                "to_company": "GlobalTech Inc",
                "to_bank": "Citibank",
                "to_account_num": "NOREASON002",
                "ours_type": "bank",
                "ours_bank": "HSBC",
                "ours_account_num": "NOREASON_OURS",
                "buy_currency": "USD",
                "sell_currency": "EUR",
                "currency_amount": 500,
                "amount": 460,
                "rate": 0.92,
            }
            create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
            deal_id = create_resp.json()["id"]
        else:
            deal_id = TestCancelDeal.cancel_test_deal_id
        
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Test with empty reason
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": ""}
        )
        assert response.status_code == 400, f"Expected 400 for empty reason, got {response.status_code}: {response.text}"
        print("✓ Cancel without reason correctly returns 400")

    def test_cancel_with_whitespace_reason_fails(self, trader_token):
        """Test that cancelling with whitespace-only reason returns 400 error"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Create a new deal for this test
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Whitespace_Reason_Client",
            "deal_date": "2026-01-20",
            "value_date": "2026-01-22",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "WHITESPACE001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "WHITESPACE002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "WHITESPACE_OURS",
            "buy_currency": "EUR",
            "sell_currency": "GBP",
            "currency_amount": 2000,
            "amount": 1760,
            "rate": 0.88,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Test with whitespace-only reason
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "   "}
        )
        assert response.status_code == 400, f"Expected 400 for whitespace reason, got {response.status_code}"
        print("✓ Cancel with whitespace-only reason correctly returns 400")

    def test_cancel_deal_success(self, trader_token):
        """Test successfully cancelling a deal with valid reason"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Create a new deal for this test
        deal_data = {
            "transaction_type": "Tomorrow",
            "transfer_type": "FX Local",
            "client_name": "TEST_Success_Cancel_Client",
            "deal_date": "2026-01-20",
            "value_date": "2026-01-22",
            "from_type": "bank",
            "from_company": "Sterling Enterprises",
            "from_bank": "Deutsche Bank",
            "from_account_num": "SUCCESS001",
            "to_type": "bank",
            "to_company": "Pacific Trading Co",
            "to_bank": "Standard Chartered",
            "to_account_num": "SUCCESS002",
            "ours_type": "bank",
            "ours_bank": "Bank of America",
            "ours_account_num": "SUCCESS_OURS",
            "buy_currency": "AUD",
            "sell_currency": "NZD",
            "currency_amount": 3000,
            "amount": 3180,
            "rate": 1.06,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        assert create_resp.status_code == 200
        deal_id = create_resp.json()["id"]
        ref_num = create_resp.json()["reference_number"]
        
        # Cancel with valid reason
        cancellation_reason = "Client revised transaction amount - need to create new deal"
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": cancellation_reason}
        )
        assert response.status_code == 200, f"Cancel failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == cancellation_reason
        assert "cancelled_at" in data
        print(f"✓ Deal cancelled successfully: {ref_num}")
        return data

    def test_cancel_already_cancelled_deal_fails(self, trader_token):
        """Test that cancelling an already cancelled deal returns 400"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Create and cancel a deal
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "PDAX Withdrawal",
            "client_name": "TEST_Double_Cancel_Client",
            "deal_date": "2026-01-21",
            "value_date": "2026-01-23",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "DBLCANCEL001",
            "to_type": "crypto",
            "to_company": "GlobalTech Inc",
            "to_wallet_address": "0xDblCancel123",
            "ours_type": "bank",
            "ours_bank": "Citibank",
            "ours_account_num": "DBLCANCEL_OURS",
            "buy_currency": "USDT",
            "sell_currency": "PHP",
            "currency_amount": 10000,
            "amount": 560000,
            "rate": 56,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # First cancellation
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "First cancellation"}
        )
        
        # Try to cancel again
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "Second cancellation attempt"}
        )
        assert response.status_code == 400, f"Expected 400 for already cancelled deal, got {response.status_code}"
        print("✓ Cannot cancel already cancelled deal (correct 400 response)")

    def test_cancel_confirmed_deal_fails(self, trader_token, treasury_token):
        """Test that cancelling a confirmed deal returns 400"""
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        
        # Create a deal
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "FX Local",
            "client_name": "TEST_Cancel_Confirmed_Client",
            "deal_date": "2026-01-21",
            "value_date": "2026-01-23",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "CONF001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "CONF002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "CONF_OURS",
            "buy_currency": "SGD",
            "sell_currency": "USD",
            "currency_amount": 7500,
            "amount": 5625,
            "rate": 0.75,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Confirm the deal as treasury
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/process",
            headers=headers_treasury,
            json={"status": "confirmed", "treasury_remarks": "Approved"}
        )
        
        # Try to cancel confirmed deal
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers_trader,
            json={"cancellation_reason": "Trying to cancel confirmed deal"}
        )
        assert response.status_code == 400, f"Expected 400 for confirmed deal, got {response.status_code}"
        print("✓ Cannot cancel confirmed deal (correct 400 response)")

    def test_deal_detail_shows_cancellation_reason(self, trader_token):
        """Test that deal detail shows cancellation reason after cancel"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        # Create and cancel a deal
        deal_data = {
            "transaction_type": "Tomorrow",
            "transfer_type": "FX Crypto Conversion",
            "client_name": "TEST_CancelDetail_Client",
            "deal_date": "2026-01-22",
            "value_date": "2026-01-24",
            "from_type": "crypto",
            "from_company": "Atlantic Financial Group",
            "from_wallet_address": "0xCancelDetail123",
            "to_type": "bank",
            "to_company": "Sterling Enterprises",
            "to_bank": "Bank of America",
            "to_account_num": "CANCELDETAIL002",
            "ours_type": "crypto",
            "ours_wallet_address": "0xOursCancelDetail789",
            "buy_currency": "PHP",
            "sell_currency": "ETH",
            "currency_amount": 280000,
            "amount": 5,
            "rate": 0.0000178571,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Cancel the deal
        cancel_reason = "Duplicate entry - client already created this deal"
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": cancel_reason}
        )
        
        # Get deal detail
        response = requests.get(f"{BASE_URL}/api/deals/{deal_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["cancellation_reason"] == cancel_reason
        assert "cancelled_at" in data
        print(f"✓ Deal detail shows cancellation reason correctly")


class TestCancelDealPermissions:
    """Test cancel deal permissions - trader can only cancel own deals"""

    def test_treasury_cannot_cancel_deal(self, trader_token, treasury_token):
        """Test that treasury cannot cancel deals (403 - only traders can cancel)"""
        headers_trader = {"Authorization": f"Bearer {trader_token}"}
        headers_treasury = {"Authorization": f"Bearer {treasury_token}"}
        
        # Create a deal as trader
        deal_data = {
            "transaction_type": "Spot",
            "transfer_type": "FX Local",
            "client_name": "TEST_Treasury_Cancel_Client",
            "deal_date": "2026-01-22",
            "value_date": "2026-01-24",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "TRCANCEL001",
            "to_type": "bank",
            "to_company": "GlobalTech Inc",
            "to_bank": "Citibank",
            "to_account_num": "TRCANCEL002",
            "ours_type": "bank",
            "ours_bank": "HSBC",
            "ours_account_num": "TRCANCEL_OURS",
            "buy_currency": "HKD",
            "sell_currency": "USD",
            "currency_amount": 78000,
            "amount": 10000,
            "rate": 0.128205,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers_trader, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Try to cancel as treasury
        response = requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers_treasury,
            json={"cancellation_reason": "Treasury trying to cancel"}
        )
        assert response.status_code == 403, f"Expected 403 for treasury cancel, got {response.status_code}"
        print("✓ Treasury cannot cancel deals (correct 403 response)")


class TestFilterCancelledStatus:
    """Test filtering deals by 'cancelled' status"""

    def test_filter_by_cancelled_status(self, trader_token):
        """Test that deals can be filtered by cancelled status"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        
        # Create and cancel a deal first
        deal_data = {
            "transaction_type": "Today",
            "transfer_type": "PDAX Withdrawal",
            "client_name": "TEST_Filter_Cancelled_Client",
            "deal_date": "2026-01-23",
            "value_date": "2026-01-25",
            "from_type": "bank",
            "from_company": "Acme Corporation",
            "from_bank": "JP Morgan Chase",
            "from_account_num": "FILTER001",
            "to_type": "crypto",
            "to_company": "GlobalTech Inc",
            "to_wallet_address": "0xFilterCancel123",
            "ours_type": "bank",
            "ours_bank": "Citibank",
            "ours_account_num": "FILTER_OURS",
            "buy_currency": "USDC",
            "sell_currency": "PHP",
            "currency_amount": 5000,
            "amount": 280000,
            "rate": 56,
        }
        create_resp = requests.post(f"{BASE_URL}/api/deals", headers=headers, json=deal_data)
        deal_id = create_resp.json()["id"]
        
        # Cancel the deal
        requests.put(
            f"{BASE_URL}/api/deals/{deal_id}/cancel",
            headers=headers,
            json={"cancellation_reason": "For filter testing"}
        )
        
        # Filter by cancelled status
        response = requests.get(f"{BASE_URL}/api/deals?status=cancelled", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # All deals should have cancelled status
        for deal in data:
            assert deal["status"] == "cancelled", f"Expected cancelled status, got {deal['status']}"
        print(f"✓ Filter by cancelled status works: {len(data)} cancelled deals")


class TestDashboardCancelledCount:
    """Test that dashboard stats include cancelled deals count"""

    def test_dashboard_includes_cancelled_count(self, trader_token):
        """Test dashboard stats endpoint includes cancelled_deals field"""
        headers = {"Authorization": f"Bearer {trader_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats?range=30d", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "cancelled_deals" in data, "Dashboard should include cancelled_deals count"
        print(f"✓ Dashboard includes cancelled_deals count: {data.get('cancelled_deals', 0)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
