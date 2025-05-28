
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
        """Test payment creation with demo mode"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "Create Payment (Demo Mode)",
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
            if response.get('demo_mode'):
                print("✅ Demo mode activated: Balance credited automatically")
            else:
                print("❌ Demo mode not activated")
        return success

    def test_create_stake(self):
        """Test stake creation with credited balance"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        # First check if user has balance
        _, user_data = self.run_test(
            "Check User Balance Before Staking",
            "GET",
            f"/api/users/{self.user_id}",
            200
        )
        
        if user_data.get('balance', 0) < 50:
            print(f"⚠️ User balance ({user_data.get('balance', 0)}) is less than 50 USDT, staking may fail")
        
        success, response = self.run_test(
            "Create Stake",
            "POST",
            "/api/stake",
            200,  # Now expecting 200 since we should have balance from demo mode
            data={
                "user_id": self.user_id,
                "amount": 50.0
            }
        )
        
        if success and 'stake_id' in response:
            self.stake_id = response['stake_id']
            print(f"Created stake with ID: {self.stake_id}")
        
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
            # Check if stakes are properly formatted
            if len(response) > 0:
                stake = response[0]
                print(f"Stake details: Amount={stake.get('amount')}, Active={stake.get('is_active')}, Earned={stake.get('total_earned')}")
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
            # Check transaction types
            tx_types = set([tx.get('type') for tx in response])
            print(f"Transaction types: {tx_types}")
        return success

    def test_unstake(self):
        """Test unstaking functionality"""
        if not self.stake_id:
            print("❌ No stake ID available for testing")
            return False
        
        success, response = self.run_test(
            "Unstake Funds",
            "POST",
            f"/api/unstake/{self.stake_id}",
            200
        )
        
        if success:
            print("Successfully unstaked funds")
            # Verify user balance after unstaking
            self.test_get_user()
        
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
            print(f"Daily APY: {response.get('daily_apy', 'N/A')}")
        return success
    
    def run_full_user_journey(self):
        """Test the complete user journey from registration to unstaking"""
        print("\n🔄 Starting complete user journey test...")
        
        # Step 1: Create new user
        if not self.test_create_user():
            print("❌ User journey failed at step 1: Create user")
            return False
            
        # Step 2: Get initial user data
        if not self.test_get_user():
            print("❌ User journey failed at step 2: Get user data")
            return False
            
        # Step 3: Create payment (demo mode should credit balance)
        if not self.test_create_payment():
            print("❌ User journey failed at step 3: Create payment")
            return False
            
        # Step 4: Verify balance was credited
        _, user_data = self.run_test(
            "Verify Balance After Deposit",
            "GET",
            f"/api/users/{self.user_id}",
            200
        )
        
        if user_data.get('balance', 0) <= 0:
            print("❌ User journey failed: Balance not credited in demo mode")
            return False
        else:
            print(f"✅ Balance credited: {user_data.get('balance')} USDT")
            
        # Step 5: Create stake
        if not self.test_create_stake():
            print("❌ User journey failed at step 5: Create stake")
            return False
            
        # Step 6: Verify stakes
        if not self.test_get_user_stakes():
            print("❌ User journey failed at step 6: Get stakes")
            return False
            
        # Step 7: Verify transactions
        if not self.test_get_user_transactions():
            print("❌ User journey failed at step 7: Get transactions")
            return False
            
        # Step 8: Unstake
        if not self.test_unstake():
            print("❌ User journey failed at step 8: Unstake")
            return False
            
        # Step 9: Final verification
        if not self.test_get_user():
            print("❌ User journey failed at step 9: Final verification")
            return False
            
        print("✅ Complete user journey test passed successfully!")
        return True

def main():
    # Setup
    tester = USDTStakingAPITester()
    
    # Run basic tests
    tester.test_root()
    
    # Run complete user journey test
    tester.run_full_user_journey()
    
    # Run platform stats test
    tester.test_get_stats()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
