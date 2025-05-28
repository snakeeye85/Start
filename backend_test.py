
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
    
    def test_user_analytics(self):
        """Test user analytics endpoint"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        success, response = self.run_test(
            "User Analytics",
            "GET",
            f"/api/users/{self.user_id}/analytics",
            200
        )
        
        if success:
            # Verify analytics structure
            if 'overview' not in response:
                print("❌ Missing 'overview' section in analytics")
                return False
                
            if 'performance' not in response:
                print("❌ Missing 'performance' section in analytics")
                return False
                
            if 'portfolio' not in response:
                print("❌ Missing 'portfolio' section in analytics")
                return False
                
            if 'projections' not in response:
                print("❌ Missing 'projections' section in analytics")
                return False
                
            if 'milestones' not in response:
                print("❌ Missing 'milestones' section in analytics")
                return False
            
            # Verify key metrics
            print(f"ROI: {response['overview'].get('roi_percentage', 'N/A')}%")
            print(f"Daily projected earnings: {response['projections'].get('daily_projected', 'N/A')} USDT")
            print(f"Monthly projected earnings: {response['projections'].get('monthly_projected', 'N/A')} USDT")
            
            # Verify daily data for charts
            daily_data = response['performance'].get('daily_data', [])
            print(f"Daily data points for charts: {len(daily_data)}")
            
            # Verify portfolio breakdown
            active_stakes = response['portfolio'].get('active_stakes', 0)
            completed_stakes = response['portfolio'].get('completed_stakes', 0)
            print(f"Portfolio: {active_stakes} active stakes, {completed_stakes} completed stakes")
            
            return True
        return False
    
    def test_platform_analytics(self):
        """Test platform analytics endpoint"""
        success, response = self.run_test(
            "Platform Analytics",
            "GET",
            "/api/analytics/platform",
            200
        )
        
        if success:
            # Verify analytics structure
            if 'overview' not in response:
                print("❌ Missing 'overview' section in platform analytics")
                return False
                
            if 'recent_activity' not in response:
                print("❌ Missing 'recent_activity' section in platform analytics")
                return False
                
            if 'daily_stats' not in response:
                print("❌ Missing 'daily_stats' section in platform analytics")
                return False
                
            if 'performance' not in response:
                print("❌ Missing 'performance' section in platform analytics")
                return False
            
            # Verify key metrics
            print(f"Total users: {response['overview'].get('total_users', 'N/A')}")
            print(f"Total staked: {response['overview'].get('total_staked', 'N/A')} USDT")
            print(f"Total rewards distributed: {response['overview'].get('total_rewards_distributed', 'N/A')} USDT")
            
            # Verify daily stats for charts
            daily_stats = response.get('daily_stats', [])
            print(f"Daily stats points for charts: {len(daily_stats)}")
            
            # Verify recent activity
            print(f"New users (7d): {response['recent_activity'].get('new_users_7d', 'N/A')}")
            print(f"New stakes (7d): {response['recent_activity'].get('new_stakes_7d', 'N/A')}")
            
            return True
        return False
    
    def verify_analytics_calculations(self):
        """Verify analytics calculations are accurate"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
            
        # Get user data
        _, user_data = self.run_test(
            "Get User Data for Calculation Verification",
            "GET",
            f"/api/users/{self.user_id}",
            200
        )
        
        # Get user analytics
        _, analytics = self.run_test(
            "Get User Analytics for Calculation Verification",
            "GET",
            f"/api/users/{self.user_id}/analytics",
            200
        )
        
        if not analytics or 'projections' not in analytics:
            print("❌ Failed to get analytics data for verification")
            return False
            
        # Verify daily projected calculation (30% of staked amount)
        staked_amount = user_data.get('staked_amount', 0)
        expected_daily = staked_amount * 0.30
        actual_daily = analytics['projections'].get('daily_projected', 0)
        
        daily_calculation_correct = abs(expected_daily - actual_daily) < 0.01
        if daily_calculation_correct:
            print(f"✅ Daily projection calculation verified: {actual_daily} USDT")
        else:
            print(f"❌ Daily projection calculation incorrect: Expected {expected_daily}, got {actual_daily}")
            
        # Verify monthly projection (daily * 30)
        expected_monthly = expected_daily * 30
        actual_monthly = analytics['projections'].get('monthly_projected', 0)
        
        monthly_calculation_correct = abs(expected_monthly - actual_monthly) < 0.01
        if monthly_calculation_correct:
            print(f"✅ Monthly projection calculation verified: {actual_monthly} USDT")
        else:
            print(f"❌ Monthly projection calculation incorrect: Expected {expected_monthly}, got {actual_monthly}")
            
        return daily_calculation_correct and monthly_calculation_correct
    
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
            
        # Step 8: Check user analytics
        if not self.test_user_analytics():
            print("❌ User journey failed at step 8: Check user analytics")
            return False
            
        # Step 9: Verify analytics calculations
        if not self.verify_analytics_calculations():
            print("❌ User journey failed at step 9: Verify analytics calculations")
            return False
            
        # Step 10: Unstake
        if not self.test_unstake():
            print("❌ User journey failed at step 10: Unstake")
            return False
            
        # Step 11: Check analytics after unstaking
        if not self.test_user_analytics():
            print("❌ User journey failed at step 11: Check analytics after unstaking")
            return False
            
        # Step 12: Final verification
        if not self.test_get_user():
            print("❌ User journey failed at step 12: Final verification")
            return False
            
        print("✅ Complete user journey test passed successfully!")
        return True
    
    def run_analytics_tests(self):
        """Run all analytics-related tests"""
        print("\n🔄 Starting analytics tests...")
        
        # Test platform analytics
        if not self.test_platform_analytics():
            print("❌ Platform analytics test failed")
            return False
            
        # Test basic stats endpoint (for backward compatibility)
        if not self.test_get_stats():
            print("❌ Basic stats endpoint test failed")
            return False
            
        # If we have a user ID, test user analytics
        if self.user_id:
            if not self.test_user_analytics():
                print("❌ User analytics test failed")
                return False
                
            if not self.verify_analytics_calculations():
                print("❌ Analytics calculations verification failed")
                return False
        else:
            print("⚠️ Skipping user analytics tests (no user ID available)")
            
        print("✅ All analytics tests passed successfully!")
        return True

def main():
    # Setup
    tester = USDTStakingAPITester()
    
    # Run basic tests
    tester.test_root()
    
    # Run analytics tests
    tester.run_analytics_tests()
    
    # Run complete user journey test with analytics
    tester.run_full_user_journey()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
