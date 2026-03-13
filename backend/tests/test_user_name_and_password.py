"""
Test suite for User Name Split (first_name + last_name) and Change Password features.
Tests the following:
1. Login returns first_name and last_name fields
2. User creation with first_name and last_name
3. User update with first_name and last_name
4. Change password - correct current password
5. Change password - wrong current password (error)
6. Change password - then revert back
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUserNameSplit:
    """Test that users have first_name and last_name fields"""
    
    def test_trader_login_returns_name_fields(self):
        """Test trader login returns first_name and last_name"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Check token exists
        assert "token" in data
        assert len(data["token"]) > 0
        
        # Check user object has first_name and last_name
        assert "user" in data
        user = data["user"]
        assert "first_name" in user, "first_name field missing from login response"
        assert "last_name" in user, "last_name field missing from login response"
        assert user["first_name"] == "John", f"Expected first_name='John', got '{user['first_name']}'"
        assert user["last_name"] == "Trader", f"Expected last_name='Trader', got '{user['last_name']}'"
        assert user["role"] == "trader"
        
    def test_treasury_login_returns_name_fields(self):
        """Test treasury login returns first_name and last_name"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "treasury@fxtracker.com",
            "password": "Treasury@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        user = data["user"]
        
        assert user["first_name"] == "Jane", f"Expected first_name='Jane', got '{user['first_name']}'"
        assert user["last_name"] == "Treasury", f"Expected last_name='Treasury', got '{user['last_name']}'"
        assert user["role"] == "treasury"
        
    def test_admin_login_returns_name_fields(self):
        """Test admin login returns first_name and last_name"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        user = data["user"]
        
        assert user["first_name"] == "System", f"Expected first_name='System', got '{user['first_name']}'"
        assert user["last_name"] == "Admin", f"Expected last_name='Admin', got '{user['last_name']}'"
        assert user["role"] == "admin"


class TestUserCRUDWithNameFields:
    """Test user CRUD with first_name and last_name fields"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@fxtracker.com",
            "password": "Admin@123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_create_user_with_name_fields(self, admin_token):
        """Test creating a user with first_name and last_name"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create user
        create_response = requests.post(f"{BASE_URL}/api/users", json={
            "email": "TEST_newuser@test.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "Test@123",
            "role": "trader"
        }, headers=headers)
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        user = create_response.json()
        
        assert user["first_name"] == "Test"
        assert user["last_name"] == "User"
        assert user["email"] == "TEST_newuser@test.com"
        assert user["role"] == "trader"
        assert "id" in user
        
        user_id = user["id"]
        
        # Verify user can login with new credentials
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "TEST_newuser@test.com",
            "password": "Test@123"
        })
        assert login_response.status_code == 200, "Created user cannot login"
        login_data = login_response.json()
        assert login_data["user"]["first_name"] == "Test"
        assert login_data["user"]["last_name"] == "User"
        
        # Cleanup - delete test user
        del_response = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        assert del_response.status_code == 200, f"Cleanup failed: {del_response.text}"
        
    def test_update_user_name_fields(self, admin_token):
        """Test updating user first_name and last_name"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create user first
        create_response = requests.post(f"{BASE_URL}/api/users", json={
            "email": "TEST_updateuser@test.com",
            "first_name": "Original",
            "last_name": "Name",
            "password": "Test@123",
            "role": "trader"
        }, headers=headers)
        
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # Update the name fields
        update_response = requests.put(f"{BASE_URL}/api/users/{user_id}", json={
            "first_name": "Updated",
            "last_name": "Person"
        }, headers=headers)
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated_user = update_response.json()
        
        assert updated_user["first_name"] == "Updated"
        assert updated_user["last_name"] == "Person"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=headers)
        
    def test_list_users_shows_name_fields(self, admin_token):
        """Test that users list returns first_name and last_name"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 200, f"List users failed: {response.text}"
        
        data = response.json()
        assert "users" in data
        assert len(data["users"]) > 0
        
        # Check that users have first_name and last_name
        for user in data["users"]:
            assert "first_name" in user, f"User {user.get('email')} missing first_name"
            assert "last_name" in user, f"User {user.get('email')} missing last_name"


class TestChangePassword:
    """Test change password functionality"""
    
    def test_change_password_wrong_current(self):
        """Test that wrong current password returns error"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Try to change password with wrong current password
        headers = {"Authorization": f"Bearer {token}"}
        change_response = requests.put(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": "WrongPassword123",
            "new_password": "NewPass123"
        }, headers=headers)
        
        assert change_response.status_code == 400, f"Expected 400, got {change_response.status_code}"
        data = change_response.json()
        assert "incorrect" in data.get("detail", "").lower() or "password" in data.get("detail", "").lower()
        
    def test_change_password_success_and_revert(self):
        """Test successful password change and revert back to original"""
        original_password = "Trader@123"
        new_password = "NewPass1"
        
        # Step 1: Login with original password
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": original_password
        })
        assert login_response.status_code == 200, "Initial login failed"
        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Change password to new password
        change_response = requests.put(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": original_password,
            "new_password": new_password
        }, headers=headers)
        
        assert change_response.status_code == 200, f"Password change failed: {change_response.text}"
        data = change_response.json()
        assert "success" in data.get("message", "").lower()
        
        # Step 3: Verify old password no longer works
        old_login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": original_password
        })
        assert old_login_response.status_code == 401, "Old password should not work"
        
        # Step 4: Verify new password works
        new_login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": new_password
        })
        assert new_login_response.status_code == 200, "New password should work"
        new_token = new_login_response.json()["token"]
        
        # Step 5: Revert password back to original
        headers = {"Authorization": f"Bearer {new_token}"}
        revert_response = requests.put(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": new_password,
            "new_password": original_password
        }, headers=headers)
        
        assert revert_response.status_code == 200, f"Password revert failed: {revert_response.text}"
        
        # Step 6: Verify original password works again
        final_login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": original_password
        })
        assert final_login_response.status_code == 200, "Original password should work after revert"
        
    def test_change_password_short_new_password(self):
        """Test that short new password is rejected"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Try to change to short password
        headers = {"Authorization": f"Bearer {token}"}
        change_response = requests.put(f"{BASE_URL}/api/auth/change-password", json={
            "current_password": "Trader@123",
            "new_password": "123"  # Too short
        }, headers=headers)
        
        assert change_response.status_code == 400, f"Expected 400, got {change_response.status_code}"


class TestAuthMe:
    """Test /auth/me endpoint returns correct user data"""
    
    def test_me_endpoint_returns_name_fields(self):
        """Test /auth/me returns first_name and last_name"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "trader@fxtracker.com",
            "password": "Trader@123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["token"]
        
        # Call /auth/me
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert me_response.status_code == 200
        user = me_response.json()
        
        assert "first_name" in user
        assert "last_name" in user
        assert user["first_name"] == "John"
        assert user["last_name"] == "Trader"
        assert user["email"] == "trader@fxtracker.com"
        assert user["role"] == "trader"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
