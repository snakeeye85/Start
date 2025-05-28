import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import { Line, Pie, Bar } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [userData, setUserData] = useState(null);
  const [stakes, setStakes] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [platformAnalytics, setPlatformAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Form states
  const [newUser, setNewUser] = useState({ name: '', email: '' });
  const [depositAmount, setDepositAmount] = useState('');
  const [stakeAmount, setStakeAmount] = useState('');
  const [loginUserId, setLoginUserId] = useState('');

  useEffect(() => {
    if (currentUser) {
      fetchUserData();
      fetchUserStakes();
      fetchUserTransactions();
      fetchUserAnalytics();
    }
    fetchPlatformAnalytics();
  }, [currentUser]);

  const fetchUserData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${currentUser}`);
      const data = await response.json();
      setUserData(data);
    } catch (error) {
      console.error('Error fetching user data:', error);
    }
  };

  const fetchUserStakes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${currentUser}/stakes`);
      const data = await response.json();
      setStakes(data);
    } catch (error) {
      console.error('Error fetching stakes:', error);
    }
  };

  const fetchUserTransactions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${currentUser}/transactions`);
      const data = await response.json();
      setTransactions(data);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const fetchUserAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${currentUser}/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchPlatformAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/platform`);
      const data = await response.json();
      setPlatformAnalytics(data);
    } catch (error) {
      console.error('Error fetching platform analytics:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      const data = await response.json();
      if (response.ok) {
        setCurrentUser(data.user_id);
        setNewUser({ name: '', email: '' });
        alert('Account created successfully!');
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('Error creating account');
    }
    setLoading(false);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${loginUserId}`);
      if (response.ok) {
        setCurrentUser(loginUserId);
        setLoginUserId('');
      } else {
        alert('User not found');
      }
    } catch (error) {
      alert('Error logging in');
    }
    setLoading(false);
  };

  const handleDeposit = async () => {
    if (!depositAmount || parseFloat(depositAmount) <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/payments/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser,
          amount: parseFloat(depositAmount)
        })
      });
      const data = await response.json();
      if (response.ok) {
        if (data.demo_mode) {
          alert('Demo Mode: Your balance has been credited automatically! You can now stake USDT.');
          setDepositAmount('');
          fetchUserData();
          fetchUserTransactions();
          fetchUserAnalytics();
        } else {
          window.open(data.payment_url, '_blank');
          setDepositAmount('');
        }
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('Error creating payment');
    }
    setLoading(false);
  };

  const handleStake = async () => {
    if (!stakeAmount || parseFloat(stakeAmount) <= 0) {
      alert('Please enter a valid amount');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/stake`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser,
          amount: parseFloat(stakeAmount)
        })
      });
      const data = await response.json();
      if (response.ok) {
        alert('Staked successfully!');
        setStakeAmount('');
        fetchUserData();
        fetchUserStakes();
        fetchUserTransactions();
        fetchUserAnalytics();
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('Error staking');
    }
    setLoading(false);
  };

  const handleUnstake = async (stakeId) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/unstake/${stakeId}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (response.ok) {
        alert('Unstaked successfully!');
        fetchUserData();
        fetchUserStakes();
        fetchUserTransactions();
        fetchUserAnalytics();
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('Error unstaking');
    }
    setLoading(false);
  };

  // Chart configurations
  const getPerformanceChartData = () => {
    if (!analytics?.performance?.daily_data) return null;
    
    const data = analytics.performance.daily_data;
    return {
      labels: data.map(d => new Date(d.date).toLocaleDateString()),
      datasets: [
        {
          label: 'Daily Rewards',
          data: data.map(d => d.daily_rewards),
          borderColor: 'rgba(34, 197, 94, 1)',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Cumulative Earnings',
          data: data.map(d => d.cumulative_earnings),
          borderColor: 'rgba(59, 130, 246, 1)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4,
          yAxisID: 'y1',
        }
      ]
    };
  };

  const getPortfolioChartData = () => {
    if (!analytics?.portfolio) return null;
    
    const portfolio = analytics.portfolio;
    return {
      labels: ['Active Stakes', 'Completed Stakes'],
      datasets: [
        {
          data: [portfolio.active_stakes, portfolio.completed_stakes],
          backgroundColor: [
            'rgba(34, 197, 94, 0.8)',
            'rgba(168, 85, 247, 0.8)',
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(168, 85, 247, 1)',
          ],
          borderWidth: 2,
        }
      ]
    };
  };

  const getPlatformChartData = () => {
    if (!platformAnalytics?.daily_stats) return null;
    
    const data = platformAnalytics.daily_stats.slice(-7); // Last 7 days
    return {
      labels: data.map(d => new Date(d.date).toLocaleDateString()),
      datasets: [
        {
          label: 'New Users',
          data: data.map(d => d.new_users),
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
        },
        {
          label: 'New Stakes',
          data: data.map(d => d.new_stakes),
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
        },
        {
          label: 'Rewards Distributed',
          data: data.map(d => d.rewards_distributed),
          backgroundColor: 'rgba(168, 85, 247, 0.8)',
        }
      ]
    };
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'white'
        }
      },
      title: {
        display: true,
        color: 'white'
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'white'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y: {
        ticks: {
          color: 'white'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        ticks: {
          color: 'white'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const pieOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: 'white'
        }
      },
    },
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center mb-12">
            <h1 className="text-6xl font-bold text-white mb-4">USDT Staking</h1>
            <p className="text-xl text-blue-200">Earn 30% Daily Returns on Your USDT</p>
          </div>
          
          <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-8">
            {/* Stats Cards */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-white">
              <h3 className="text-2xl font-bold mb-4">Platform Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Total Users:</span>
                  <span className="font-bold">{platformAnalytics?.overview?.total_users || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Staked:</span>
                  <span className="font-bold">{platformAnalytics?.overview?.total_staked?.toFixed(2) || '0.00'} USDT</span>
                </div>
                <div className="flex justify-between">
                  <span>Rewards Distributed:</span>
                  <span className="font-bold">{platformAnalytics?.overview?.total_rewards_distributed?.toFixed(2) || '0.00'} USDT</span>
                </div>
                <div className="flex justify-between">
                  <span>Daily APY:</span>
                  <span className="font-bold text-green-400">30%</span>
                </div>
              </div>
            </div>

            {/* Login/Register Forms */}
            <div className="space-y-6">
              {/* Create Account */}
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
                <h3 className="text-2xl font-bold text-white mb-4">Create Account</h3>
                <form onSubmit={handleCreateUser} className="space-y-4">
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={newUser.name}
                    onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                    className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-white/70 border border-white/30"
                    required
                  />
                  <input
                    type="email"
                    placeholder="Email Address"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-white/70 border border-white/30"
                    required
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-3 rounded-lg font-bold hover:from-green-600 hover:to-blue-600 transition-all disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Account'}
                  </button>
                </form>
              </div>

              {/* Login */}
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
                <h3 className="text-2xl font-bold text-white mb-4">Login</h3>
                <form onSubmit={handleLogin} className="space-y-4">
                  <input
                    type="text"
                    placeholder="Enter your User ID"
                    value={loginUserId}
                    onChange={(e) => setLoginUserId(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-white/70 border border-white/30"
                    required
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-bold hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mb-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white">USDT Staking Dashboard</h1>
            <button
              onClick={() => setCurrentUser(null)}
              className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
          {userData && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-white">
              <div className="text-center">
                <p className="text-sm opacity-70">Balance</p>
                <p className="text-xl font-bold">{userData.balance?.toFixed(2)} USDT</p>
              </div>
              <div className="text-center">
                <p className="text-sm opacity-70">Staked</p>
                <p className="text-xl font-bold">{userData.staked_amount?.toFixed(2)} USDT</p>
              </div>
              <div className="text-center">
                <p className="text-sm opacity-70">Total Rewards</p>
                <p className="text-xl font-bold text-green-400">{userData.total_rewards?.toFixed(2)} USDT</p>
              </div>
              <div className="text-center">
                <p className="text-sm opacity-70">ROI</p>
                <p className="text-xl font-bold text-green-400">{analytics?.overview?.roi_percentage?.toFixed(1) || 0}%</p>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 overflow-x-auto">
          {['dashboard', 'analytics', 'deposit', 'stake', 'transactions'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-lg font-medium capitalize transition-all whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-white text-purple-900'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'dashboard' && (
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <h3 className="text-2xl font-bold text-white mb-4">Active Stakes</h3>
              <div className="space-y-4">
                {stakes.filter(s => s.is_active).map((stake) => (
                  <div key={stake.id} className="bg-white/10 rounded-lg p-4">
                    <div className="flex justify-between items-center text-white">
                      <div>
                        <p className="font-bold">{stake.amount} USDT</p>
                        <p className="text-sm opacity-70">Earned: {stake.total_earned?.toFixed(2)} USDT</p>
                        <p className="text-sm opacity-70">Started: {new Date(stake.start_date).toLocaleDateString()}</p>
                      </div>
                      <button
                        onClick={() => handleUnstake(stake.id)}
                        disabled={loading}
                        className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
                      >
                        Unstake
                      </button>
                    </div>
                  </div>
                ))}
                {stakes.filter(s => s.is_active).length === 0 && (
                  <p className="text-white/70 text-center py-8">No active stakes</p>
                )}
              </div>
            </div>

            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <h3 className="text-2xl font-bold text-white mb-4">Performance Overview</h3>
              {analytics && (
                <div className="space-y-4 text-white">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                      <p className="text-sm opacity-70">Total Invested</p>
                      <p className="text-lg font-bold">{analytics.overview?.total_invested?.toFixed(2)} USDT</p>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                      <p className="text-sm opacity-70">Total Earned</p>
                      <p className="text-lg font-bold text-green-400">{analytics.overview?.total_earned?.toFixed(2)} USDT</p>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                      <p className="text-sm opacity-70">Daily Projected</p>
                      <p className="text-lg font-bold text-blue-400">{analytics.projections?.daily_projected?.toFixed(2)} USDT</p>
                    </div>
                    <div className="bg-white/10 rounded-lg p-3 text-center">
                      <p className="text-sm opacity-70">Monthly Projected</p>
                      <p className="text-lg font-bold text-purple-400">{analytics.projections?.monthly_projected?.toFixed(2)} USDT</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <button
                      onClick={() => setActiveTab('deposit')}
                      className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-3 rounded-lg font-bold hover:from-green-600 hover:to-blue-600 transition-all"
                    >
                      Deposit USDT
                    </button>
                    <button
                      onClick={() => setActiveTab('stake')}
                      className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-bold hover:from-purple-600 hover:to-pink-600 transition-all"
                    >
                      Stake USDT
                    </button>
                  </div>
                  
                  <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4">
                    <p className="text-yellow-300 text-sm font-medium">
                      💡 Daily rewards are automatically distributed every 24 hours at 30% APY
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-8">
            {/* Performance Charts */}
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
                <h3 className="text-2xl font-bold text-white mb-4">Performance Timeline</h3>
                {getPerformanceChartData() && (
                  <div className="h-64">
                    <Line data={getPerformanceChartData()} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: true, text: 'Daily & Cumulative Rewards', color: 'white'}}}} />
                  </div>
                )}
              </div>

              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
                <h3 className="text-2xl font-bold text-white mb-4">Portfolio Distribution</h3>
                {getPortfolioChartData() && (
                  <div className="h-64">
                    <Pie data={getPortfolioChartData()} options={pieOptions} />
                  </div>
                )}
              </div>
            </div>

            {/* Analytics Cards */}
            {analytics && (
              <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-white">
                  <h4 className="text-lg font-bold mb-3">🎯 Milestones</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Biggest Stake:</span>
                      <span className="font-bold">{analytics.milestones?.biggest_stake?.toFixed(2)} USDT</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Total Transactions:</span>
                      <span className="font-bold">{analytics.milestones?.total_transactions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Rewards Received:</span>
                      <span className="font-bold">{analytics.milestones?.reward_transactions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Days Active:</span>
                      <span className="font-bold">{analytics.overview?.days_active}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-white">
                  <h4 className="text-lg font-bold mb-3">📈 Performance</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Best Day:</span>
                      <span className="font-bold text-green-400">{analytics.performance?.best_day?.toFixed(2)} USDT</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Average Daily:</span>
                      <span className="font-bold">{analytics.performance?.average_daily?.toFixed(2)} USDT</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">ROI:</span>
                      <span className="font-bold text-green-400">{analytics.overview?.roi_percentage?.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Active Stakes:</span>
                      <span className="font-bold">{analytics.portfolio?.active_stakes}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 text-white">
                  <h4 className="text-lg font-bold mb-3">🔮 Projections</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Weekly:</span>
                      <span className="font-bold text-blue-400">{analytics.projections?.weekly_projected?.toFixed(2)} USDT</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Monthly:</span>
                      <span className="font-bold text-purple-400">{analytics.projections?.monthly_projected?.toFixed(2)} USDT</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm opacity-70">Yearly:</span>
                      <span className="font-bold text-yellow-400">{analytics.projections?.yearly_projected?.toFixed(2)} USDT</span>
                    </div>
                    <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-2 mt-3">
                      <p className="text-green-300 text-xs text-center">
                        Based on current staked amount
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Platform Analytics */}
            {platformAnalytics && (
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
                <h3 className="text-2xl font-bold text-white mb-4">Platform Analytics (Last 7 Days)</h3>
                <div className="h-64 mb-4">
                  {getPlatformChartData() && (
                    <Bar data={getPlatformChartData()} options={{...chartOptions, plugins: {...chartOptions.plugins, title: {display: true, text: 'Platform Activity', color: 'white'}}}} />
                  )}
                </div>
                <div className="grid md:grid-cols-3 gap-4 text-white">
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <p className="text-sm opacity-70">New Users (7d)</p>
                    <p className="text-xl font-bold">{platformAnalytics.recent_activity?.new_users_7d}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <p className="text-sm opacity-70">New Stakes (7d)</p>
                    <p className="text-xl font-bold">{platformAnalytics.recent_activity?.new_stakes_7d}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <p className="text-sm opacity-70">Transactions (7d)</p>
                    <p className="text-xl font-bold">{platformAnalytics.recent_activity?.transactions_7d}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'deposit' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <h3 className="text-2xl font-bold text-white mb-4">Deposit USDT</h3>
              <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4 mb-4">
                <p className="text-blue-300 text-sm font-medium">
                  🚀 Demo Mode Active: For testing, your balance will be credited automatically
                </p>
              </div>
              <div className="space-y-4">
                <input
                  type="number"
                  placeholder="Amount in USD"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-white/70 border border-white/30"
                  min="1"
                  step="0.01"
                />
                <button
                  onClick={handleDeposit}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-3 rounded-lg font-bold hover:from-green-600 hover:to-blue-600 transition-all disabled:opacity-50"
                >
                  {loading ? 'Creating Payment...' : 'Deposit with USDT (Demo)'}
                </button>
                <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4">
                  <p className="text-blue-300 text-sm">
                    💳 In production, you'll be redirected to NOWPayments to complete your USDT deposit securely
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'stake' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
              <h3 className="text-2xl font-bold text-white mb-4">Stake USDT</h3>
              <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 mb-4">
                <p className="text-green-300 text-sm font-medium">
                  🚀 Earn 30% daily returns on your staked USDT!
                </p>
              </div>
              <div className="space-y-4">
                <input
                  type="number"
                  placeholder="Amount to stake"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-white/20 text-white placeholder-white/70 border border-white/30"
                  min="1"
                  step="0.01"
                  max={userData?.balance || 0}
                />
                <p className="text-white/70 text-sm">
                  Available balance: {userData?.balance?.toFixed(2) || '0.00'} USDT
                </p>
                {analytics && (
                  <div className="bg-white/10 rounded-lg p-4">
                    <h4 className="text-white font-bold mb-2">Expected Returns</h4>
                    <div className="grid grid-cols-3 gap-4 text-white text-sm">
                      <div className="text-center">
                        <p className="opacity-70">Daily</p>
                        <p className="font-bold">{(parseFloat(stakeAmount || 0) * 0.30).toFixed(2)} USDT</p>
                      </div>
                      <div className="text-center">
                        <p className="opacity-70">Weekly</p>
                        <p className="font-bold">{(parseFloat(stakeAmount || 0) * 0.30 * 7).toFixed(2)} USDT</p>
                      </div>
                      <div className="text-center">
                        <p className="opacity-70">Monthly</p>
                        <p className="font-bold">{(parseFloat(stakeAmount || 0) * 0.30 * 30).toFixed(2)} USDT</p>
                      </div>
                    </div>
                  </div>
                )}
                <button
                  onClick={handleStake}
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-3 rounded-lg font-bold hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50"
                >
                  {loading ? 'Staking...' : 'Stake Now'}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'transactions' && (
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6">
            <h3 className="text-2xl font-bold text-white mb-4">Transaction History</h3>
            <div className="space-y-3">
              {transactions.map((tx) => (
                <div key={tx.id} className="bg-white/10 rounded-lg p-4 flex justify-between items-center">
                  <div className="text-white">
                    <p className="font-medium capitalize flex items-center">
                      {tx.type}
                      {tx.type === 'deposit' && '💰'}
                      {tx.type === 'stake' && '🔒'}
                      {tx.type === 'unstake' && '🔓'}
                      {tx.type === 'reward' && '🎁'}
                    </p>
                    <p className="text-sm opacity-70">{new Date(tx.created_at).toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold ${tx.type === 'deposit' || tx.type === 'reward' ? 'text-green-400' : 'text-red-400'}`}>
                      {tx.type === 'deposit' || tx.type === 'reward' ? '+' : '-'}{tx.amount?.toFixed(2)} USDT
                    </p>
                    <p className={`text-sm capitalize ${tx.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                      {tx.status}
                    </p>
                  </div>
                </div>
              ))}
              {transactions.length === 0 && (
                <p className="text-white/70 text-center py-8">No transactions yet</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;