
import requests
import sys
import time
import uuid
from datetime import datetime

class USDTStakingAPITester:
    def __init__(self, base_url="https://3f9e7843-9200-4cf3-b121-43130896d056.preview.emergentagent.com"):
        self.base_url = base_url
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.stake_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root(self):
        """Test root endpoint"""
        return self.run_test(
            "Root Endpoint",
            "GET",
            "/",
            200
        )

    def test_create_user(self):
        """Test user creation"""
        unique_id = str(uuid.uuid4())[:8]
        success, response = self.run_test(
            "Create User",
            "POST",
            "/api/users",
            200,
            data={
                "email": f"test{unique_id}@example.com",
                "name": f"Test User {unique_id}"
            }
        )
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            print(f"Created user with ID: {self.user_id}")
        return success

    def test_get_user(self):
        """Test getting user data"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Get User Data",
            "GET",
            f"/api/users/{self.user_id}",
            200
        )
        if success:
            print(f"User data: Balance={response.get('balance', 'N/A')}, Name={response.get('name', 'N/A')}")
        return success

    def test_create_payment(self):
        """Test payment creation"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Create Payment",
            "POST",
            "/api/payments/create",
            200,
            data={
                "user_id": self.user_id,
                "amount": 100.0
            }
        )
        if success:
            print(f"Payment URL: {response.get('payment_url', 'N/A')}")
            print(f"Payment ID: {response.get('payment_id', 'N/A')}")
        return success

    def test_create_stake(self):
        """Test stake creation (this will fail without balance)"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Create Stake (Expected to fail without balance)",
            "POST",
            "/api/stake",
            400,  # Expecting 400 since we have no balance
            data={
                "user_id": self.user_id,
                "amount": 50.0
            }
        )
        return success

    def test_get_user_stakes(self):
        """Test getting user stakes"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Get User Stakes",
            "GET",
            f"/api/users/{self.user_id}/stakes",
            200
        )
        if success:
            print(f"User has {len(response)} stakes")
        return success

    def test_get_user_transactions(self):
        """Test getting user transactions"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Get User Transactions",
            "GET",
            f"/api/users/{self.user_id}/transactions",
            200
        )
        if success:
            print(f"User has {len(response)} transactions")
        return success

    def test_get_stats(self):
        """Test getting platform stats"""
        success, response = self.run_test(
            "Get Platform Stats",
            "GET",
            "/api/stats",
            200
        )
        if success:
            print(f"Platform stats: Users={response.get('total_users', 'N/A')}, Staked={response.get('total_staked', 'N/A')}")
        return success

def main():
    # Setup
    tester = USDTStakingAPITester()
    
    # Run tests
    tester.test_root()
    tester.test_create_user()
    tester.test_get_user()
    tester.test_create_payment()
    tester.test_get_user_stakes()
    tester.test_get_user_transactions()
    tester.test_create_stake()
    tester.test_get_stats()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
