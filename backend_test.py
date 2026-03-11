#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class FXTradingAPITester:
    def __init__(self):
        self.base_url = "https://forex-ticket-hub.preview.emergentagent.com/api"
        self.tokens = {}  # Store tokens for different users
        self.users = [
            {"email": "admin@fxtracker.com", "password": "Admin@123", "role": "admin"},
            {"email": "trader@fxtracker.com", "password": "Trader@123", "role": "trader"},
            {"email": "treasury@fxtracker.com", "password": "Treasury@123", "role": "treasury"}
        ]
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.reference_data = {}
        self.test_deal_id = None

    def log(self, message: str, status: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbol = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"[{timestamp}] {status_symbol.get(status, 'ℹ️')} {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, params: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return response.status_code < 400, response.json() if response.text else {}, response.status_code
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {str(e)}", "error")
            return False, {"error": str(e)}, 0
        except json.JSONDecodeError:
            return response.status_code < 400, {"raw_response": response.text}, response.status_code

    def run_test(self, name: str, test_func) -> bool:
        """Run a single test function"""
        self.tests_run += 1
        self.log(f"Testing: {name}")
        
        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                self.log(f"PASSED: {name}", "success")
            else:
                self.failed_tests.append(name)
                self.log(f"FAILED: {name}", "error")
            return result
        except Exception as e:
            self.failed_tests.append(f"{name} - Exception: {str(e)}")
            self.log(f"FAILED: {name} - {str(e)}", "error")
            return False

    def test_authentication(self) -> bool:
        """Test login functionality for all user roles"""
        success_count = 0
        
        for user in self.users:
            success, data, status = self.make_request('POST', '/auth/login', {
                'email': user['email'],
                'password': user['password']
            })
            
            if success and 'token' in data and data.get('user', {}).get('role') == user['role']:
                self.tokens[user['role']] = data['token']
                success_count += 1
                self.log(f"Login successful for {user['role']}: {user['email']}")
            else:
                self.log(f"Login failed for {user['role']}: {data}", "error")
        
        return success_count == len(self.users)

    def test_user_profile(self) -> bool:
        """Test /auth/me endpoint for each role"""
        success_count = 0
        
        for role, token in self.tokens.items():
            success, data, status = self.make_request('GET', '/auth/me', token=token)
            
            if success and data.get('role') == role:
                success_count += 1
                self.log(f"Profile fetch successful for {role}")
            else:
                self.log(f"Profile fetch failed for {role}: {data}", "error")
        
        return success_count == len(self.tokens)

    def test_reference_data_fetch(self) -> bool:
        """Test fetching reference data (available to all roles)"""
        ref_types = ['companies', 'banks', 'transaction-types', 'transfer-types', 'currencies']
        success_count = 0
        
        token = self.tokens.get('trader')  # Use trader token
        if not token:
            return False
        
        for ref_type in ref_types:
            success, data, status = self.make_request('GET', f'/reference/{ref_type}', token=token)
            
            if success and isinstance(data, list):
                self.reference_data[ref_type] = data
                success_count += 1
                self.log(f"Reference data for {ref_type}: {len(data)} items")
            else:
                self.log(f"Failed to fetch {ref_type}: {data}", "error")
        
        return success_count == len(ref_types)

    def test_admin_user_management(self) -> bool:
        """Test user management operations (admin only)"""
        admin_token = self.tokens.get('admin')
        if not admin_token:
            return False
        
        # Test fetching users
        success, users_data, status = self.make_request('GET', '/users', token=admin_token)
        if not success or not isinstance(users_data, list):
            self.log(f"Failed to fetch users: {users_data}", "error")
            return False
        
        self.log(f"Fetched {len(users_data)} users")
        
        # Test creating a new user
        new_user_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"testuser{datetime.now().strftime('%H%M%S')}@fxtracker.com",
            "password": "TestUser@123",
            "role": "trader"
        }
        
        success, created_user, status = self.make_request('POST', '/users', new_user_data, token=admin_token)
        if success and created_user.get('id'):
            self.log(f"Created test user: {created_user['email']}")
            
            # Clean up - delete the test user
            user_id = created_user['id']
            success_del, _, _ = self.make_request('DELETE', f'/users/{user_id}', token=admin_token)
            if success_del:
                self.log(f"Cleaned up test user")
            
            return True
        else:
            self.log(f"Failed to create user: {created_user}", "error")
            return False

    def test_admin_reference_data_management(self) -> bool:
        """Test reference data CRUD operations (admin only)"""
        admin_token = self.tokens.get('admin')
        if not admin_token:
            return False
        
        # Test creating a new company
        test_company = {
            "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "code": f"TEST{datetime.now().strftime('%H%M%S')}"
        }
        
        success, created_company, status = self.make_request('POST', '/reference/companies', test_company, token=admin_token)
        if success and created_company.get('id'):
            self.log(f"Created test company: {created_company['name']}")
            
            # Test updating the company
            update_data = {"name": f"Updated {test_company['name']}"}
            success_upd, updated_company, _ = self.make_request('PUT', f'/reference/companies/{created_company["id"]}', update_data, token=admin_token)
            
            if success_upd:
                self.log(f"Updated test company")
            
            # Clean up - delete the test company
            success_del, _, _ = self.make_request('DELETE', f'/reference/companies/{created_company["id"]}', token=admin_token)
            if success_del:
                self.log(f"Cleaned up test company")
            
            return success_upd
        else:
            self.log(f"Failed to create test company: {created_company}", "error")
            return False

    def test_trader_deal_creation(self) -> bool:
        """Test deal creation by trader"""
        trader_token = self.tokens.get('trader')
        if not trader_token:
            return False
        
        # Get reference data for the deal
        companies = self.reference_data.get('companies', [])
        banks = self.reference_data.get('banks', [])
        tx_types = self.reference_data.get('transaction-types', [])
        tf_types = self.reference_data.get('transfer-types', [])
        currencies = self.reference_data.get('currencies', [])
        
        if not all([companies, banks, tx_types, tf_types, currencies]):
            self.log("Missing reference data for deal creation", "error")
            return False
        
        # Create test deal
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        deal_data = {
            "transaction_type": tx_types[0]['name'],
            "transfer_type": tf_types[0]['name'],
            "deal_date": today,
            "value_date": tomorrow,
            "from_company": companies[0]['name'],
            "from_bank": banks[0]['name'],
            "from_account_num": "1234567890",
            "to_company": companies[-1]['name'] if len(companies) > 1 else companies[0]['name'],
            "to_bank": banks[-1]['name'] if len(banks) > 1 else banks[0]['name'],
            "to_account_num": "0987654321",
            "buy_currency": "USD",
            "sell_currency": "EUR",
            "currency_amount": 100000.0,
            "amount": 85000.0,
            "rate": 0.85,
            "remarks": "Test deal created by automated test"
        }
        
        success, created_deal, status = self.make_request('POST', '/deals', deal_data, token=trader_token)
        if success and created_deal.get('id'):
            self.test_deal_id = created_deal['id']
            self.log(f"Created test deal: {created_deal['reference_number']}")
            return True
        else:
            self.log(f"Failed to create deal: {created_deal}", "error")
            return False

    def test_trader_deal_listing(self) -> bool:
        """Test deal listing for trader"""
        trader_token = self.tokens.get('trader')
        if not trader_token:
            return False
        
        success, deals, status = self.make_request('GET', '/deals', token=trader_token)
        if success and isinstance(deals, list):
            self.log(f"Trader can see {len(deals)} deals")
            
            # Test status filtering
            success_filt, pending_deals, _ = self.make_request('GET', '/deals', token=trader_token, params={'status': 'pending'})
            if success_filt:
                self.log(f"Filtered pending deals: {len(pending_deals)}")
                return True
        
        self.log(f"Failed to list deals: {deals}", "error")
        return False

    def test_treasury_deal_processing(self) -> bool:
        """Test deal processing by treasury operations"""
        treasury_token = self.tokens.get('treasury')
        if not treasury_token or not self.test_deal_id:
            return False
        
        # Treasury should see all deals
        success, all_deals, status = self.make_request('GET', '/deals', token=treasury_token)
        if not success:
            self.log(f"Treasury failed to fetch deals: {all_deals}", "error")
            return False
        
        self.log(f"Treasury can see {len(all_deals)} deals")
        
        # Process the test deal
        process_data = {
            "status": "confirmed",
            "treasury_remarks": "Deal confirmed by automated test"
        }
        
        success, processed_deal, status = self.make_request('PUT', f'/deals/{self.test_deal_id}/process', process_data, token=treasury_token)
        if success and processed_deal.get('status') == 'confirmed':
            self.log(f"Deal processed successfully: {processed_deal['reference_number']}")
            return True
        else:
            self.log(f"Failed to process deal: {processed_deal}", "error")
            return False

    def test_dashboard_stats(self) -> bool:
        """Test dashboard statistics for different roles"""
        success_count = 0
        
        for role, token in self.tokens.items():
            success, stats, status = self.make_request('GET', '/dashboard/stats', token=token, params={'range': '30d'})
            
            if success and isinstance(stats, dict):
                required_fields = ['total_deals', 'pending_deals', 'confirmed_deals', 'returned_deals']
                if all(field in stats for field in required_fields):
                    success_count += 1
                    self.log(f"Dashboard stats for {role}: {stats['total_deals']} total deals")
                else:
                    self.log(f"Missing stats fields for {role}: {stats}", "error")
            else:
                self.log(f"Failed to get stats for {role}: {stats}", "error")
        
        return success_count == len(self.tokens)

    def test_authorization_controls(self) -> bool:
        """Test role-based access controls"""
        trader_token = self.tokens.get('trader')
        treasury_token = self.tokens.get('treasury')
        
        if not trader_token or not treasury_token:
            return False
        
        # Trader should NOT be able to access user management
        success, response, status = self.make_request('GET', '/users', token=trader_token)
        trader_blocked = not success and status == 403
        
        # Treasury should NOT be able to create users
        test_user = {"name": "Test", "email": "test@test.com", "password": "test", "role": "trader"}
        success, response, status = self.make_request('POST', '/users', test_user, token=treasury_token)
        treasury_blocked = not success and status == 403
        
        # Treasury should NOT be able to manage reference data
        success, response, status = self.make_request('POST', '/reference/companies', {"name": "Test", "code": "TEST"}, token=treasury_token)
        treasury_ref_blocked = not success and status == 403
        
        if trader_blocked and treasury_blocked and treasury_ref_blocked:
            self.log("Authorization controls working correctly")
            return True
        else:
            self.log("Authorization control failures detected", "error")
            return False

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("Starting FX Trading Tracker API Tests", "info")
        self.log(f"Testing against: {self.base_url}", "info")
        
        # Test sequence
        test_sequence = [
            ("Authentication (All Roles)", self.test_authentication),
            ("User Profile Access", self.test_user_profile),
            ("Reference Data Fetching", self.test_reference_data_fetch),
            ("Admin User Management", self.test_admin_user_management),
            ("Admin Reference Data Management", self.test_admin_reference_data_management),
            ("Trader Deal Creation", self.test_trader_deal_creation),
            ("Trader Deal Listing", self.test_trader_deal_listing),
            ("Treasury Deal Processing", self.test_treasury_deal_processing),
            ("Dashboard Statistics", self.test_dashboard_stats),
            ("Authorization Controls", self.test_authorization_controls),
        ]
        
        for test_name, test_func in test_sequence:
            self.run_test(test_name, test_func)
            print()  # Add spacing between tests
        
        # Print summary
        print("=" * 60)
        self.log(f"Tests completed: {self.tests_passed}/{self.tests_run} passed", "info")
        
        if self.failed_tests:
            self.log("Failed tests:", "error")
            for failed_test in self.failed_tests:
                self.log(f"  - {failed_test}", "error")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        self.log(f"Success rate: {success_rate:.1f}%", "success" if success_rate >= 80 else "warning")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FXTradingAPITester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())