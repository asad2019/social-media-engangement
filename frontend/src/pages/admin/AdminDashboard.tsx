import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/ui/Button';
import Card, { CardBody, CardHeader } from '../../components/ui/Card';

interface SystemStats {
  totalUsers: number;
  activeUsers: number;
  totalCampaigns: number;
  activeCampaigns: number;
  totalJobs: number;
  completedJobs: number;
  totalRevenue: number;
  pendingPayouts: number;
  flaggedItems: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
}

interface RecentActivity {
  id: string;
  type: 'user_registration' | 'campaign_created' | 'job_completed' | 'payment_processed' | 'flag_created' | 'admin_action';
  description: string;
  timestamp: string;
  user?: string;
  severity: 'low' | 'medium' | 'high';
}

interface FlaggedItem {
  id: string;
  type: 'job_attempt' | 'user_report' | 'payment_dispute' | 'fraud_detection';
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_review' | 'resolved' | 'dismissed';
  createdAt: string;
  assignedTo?: string;
}

interface UserManagement {
  totalUsers: number;
  promoters: number;
  earners: number;
  admins: number;
  suspendedUsers: number;
  pendingKYC: number;
  verifiedUsers: number;
}

const AdminDashboard: React.FC = () => {
  const [systemStats, setSystemStats] = useState<SystemStats>({
    totalUsers: 15420,
    activeUsers: 12350,
    totalCampaigns: 2850,
    activeCampaigns: 450,
    totalJobs: 45600,
    completedJobs: 42100,
    totalRevenue: 125000.75,
    pendingPayouts: 8500.25,
    flaggedItems: 23,
    systemHealth: 'healthy'
  });

  const [userManagement, setUserManagement] = useState<UserManagement>({
    totalUsers: 15420,
    promoters: 2850,
    earners: 12570,
    admins: 12,
    suspendedUsers: 45,
    pendingKYC: 125,
    verifiedUsers: 15275
  });

  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([
    {
      id: '1',
      type: 'user_registration',
      description: 'New user registered: @fashionista_2024',
      timestamp: '2024-01-20T10:30:00Z',
      user: 'fashionista_2024',
      severity: 'low'
    },
    {
      id: '2',
      type: 'campaign_created',
      description: 'New campaign created: "Instagram Fashion Campaign"',
      timestamp: '2024-01-20T09:15:00Z',
      user: 'promoter_123',
      severity: 'medium'
    },
    {
      id: '3',
      type: 'flag_created',
      description: 'Job attempt flagged for review',
      timestamp: '2024-01-20T08:45:00Z',
      user: 'earner_456',
      severity: 'high'
    },
    {
      id: '4',
      type: 'payment_processed',
      description: 'Payout processed: $150.00 to @techlover99',
      timestamp: '2024-01-20T08:30:00Z',
      user: 'techlover99',
      severity: 'medium'
    },
    {
      id: '5',
      type: 'admin_action',
      description: 'User @spammer_account suspended',
      timestamp: '2024-01-20T07:20:00Z',
      user: 'admin_user',
      severity: 'high'
    }
  ]);

  const [flaggedItems, setFlaggedItems] = useState<FlaggedItem[]>([
    {
      id: '1',
      type: 'job_attempt',
      description: 'Suspicious screenshot detected in Instagram like job',
      priority: 'high',
      status: 'pending',
      createdAt: '2024-01-20T10:00:00Z'
    },
    {
      id: '2',
      type: 'user_report',
      description: 'User reported for inappropriate behavior',
      priority: 'medium',
      status: 'in_review',
      createdAt: '2024-01-20T09:30:00Z',
      assignedTo: 'admin_moderator'
    },
    {
      id: '3',
      type: 'fraud_detection',
      description: 'Multiple accounts detected from same IP',
      priority: 'critical',
      status: 'pending',
      createdAt: '2024-01-20T09:00:00Z'
    },
    {
      id: '4',
      type: 'payment_dispute',
      description: 'Chargeback dispute from Stripe',
      priority: 'high',
      status: 'pending',
      createdAt: '2024-01-20T08:45:00Z'
    }
  ]);

  const [quickActions] = useState([
    {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: '👥',
      link: '/admin/users',
      color: 'bg-primary-500'
    },
    {
      title: 'Campaign Oversight',
      description: 'Monitor and manage campaigns',
      icon: '📊',
      link: '/admin/campaigns',
      color: 'bg-secondary-500'
    },
    {
      title: 'Financial Control',
      description: 'Manage payments and withdrawals',
      icon: '💰',
      link: '/admin/financial',
      color: 'bg-success-500'
    },
    {
      title: 'Manual Review',
      description: 'Review flagged items and disputes',
      icon: '🔍',
      link: '/admin/review',
      color: 'bg-warning-500'
    },
    {
      title: 'System Settings',
      description: 'Configure platform settings',
      icon: '⚙️',
      link: '/admin/settings',
      color: 'bg-info-500'
    },
    {
      title: 'Analytics & Reports',
      description: 'View detailed analytics and reports',
      icon: '📈',
      link: '/admin/analytics',
      color: 'bg-accent-500'
    }
  ]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'badge-secondary';
      case 'medium': return 'badge-warning';
      case 'high': return 'badge-error';
      default: return 'badge-secondary';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'low': return 'badge-secondary';
      case 'medium': return 'badge-warning';
      case 'high': return 'badge-error';
      case 'critical': return 'bg-red-600 text-white';
      default: return 'badge-secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'badge-warning';
      case 'in_review': return 'badge-info';
      case 'resolved': return 'badge-success';
      case 'dismissed': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  };

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-success-600';
      case 'warning': return 'text-warning-600';
      case 'critical': return 'text-error-600';
      default: return 'text-neutral-600';
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Admin Dashboard</h1>
              <p className="text-neutral-600">System overview and management controls</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${systemStats.systemHealth === 'healthy' ? 'bg-success-500' : systemStats.systemHealth === 'warning' ? 'bg-warning-500' : 'bg-error-500'}`}></div>
                <span className={`text-sm font-medium ${getHealthColor(systemStats.systemHealth)}`}>
                  System {systemStats.systemHealth.charAt(0).toUpperCase() + systemStats.systemHealth.slice(1)}
                </span>
              </div>
              <Button variant="secondary">System Logs</Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* System Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Users</p>
                  <p className="text-2xl font-bold text-neutral-900">{systemStats.totalUsers.toLocaleString()}</p>
                  <p className="text-xs text-success-600">+{systemStats.activeUsers.toLocaleString()} active</p>
                </div>
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">👥</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Active Campaigns</p>
                  <p className="text-2xl font-bold text-primary-600">{systemStats.activeCampaigns}</p>
                  <p className="text-xs text-neutral-500">{systemStats.totalCampaigns} total</p>
                </div>
                <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Completed Jobs</p>
                  <p className="text-2xl font-bold text-success-600">{systemStats.completedJobs.toLocaleString()}</p>
                  <p className="text-xs text-neutral-500">{systemStats.totalJobs.toLocaleString()} total</p>
                </div>
                <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">✅</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Revenue</p>
                  <p className="text-2xl font-bold text-accent-600">${systemStats.totalRevenue.toLocaleString()}</p>
                  <p className="text-xs text-warning-600">${systemStats.pendingPayouts.toLocaleString()} pending</p>
                </div>
                <div className="w-12 h-12 bg-accent-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">💰</span>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quickActions.map((action, index) => (
              <Link key={index} to={action.link}>
                <Card hover className="cursor-pointer">
                  <CardBody>
                    <div className="flex items-center space-x-4">
                      <div className={`w-12 h-12 ${action.color} rounded-lg flex items-center justify-center text-white text-xl`}>
                        {action.icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-neutral-900">{action.title}</h3>
                        <p className="text-sm text-neutral-600">{action.description}</p>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Flagged Items */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-neutral-900">Flagged Items</h2>
            <Link to="/admin/review">
              <Button variant="secondary" size="sm">View All</Button>
            </Link>
          </div>
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Items Requiring Review</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                {flaggedItems.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`badge ${getPriorityColor(item.priority)}`}>
                          {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                        </span>
                        <span className={`badge ${getStatusColor(item.status)}`}>
                          {item.status.replace('_', ' ').charAt(0).toUpperCase() + item.status.replace('_', ' ').slice(1)}
                        </span>
                        <span className="text-sm text-neutral-500">
                          {item.type.replace('_', ' ').charAt(0).toUpperCase() + item.type.replace('_', ' ').slice(1)}
                        </span>
                      </div>
                      <p className="text-neutral-900 font-medium">{item.description}</p>
                      <p className="text-sm text-neutral-500">
                        Created: {new Date(item.createdAt).toLocaleString()}
                        {item.assignedTo && ` • Assigned to: ${item.assignedTo}`}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <Button size="sm" variant="secondary">Review</Button>
                      <Button size="sm">Resolve</Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>

        {/* User Management Overview */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 mb-4">User Management</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardBody>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-600 mb-2">{userManagement.promoters}</div>
                  <p className="text-neutral-600">Promoters</p>
                </div>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <div className="text-center">
                  <div className="text-3xl font-bold text-secondary-600 mb-2">{userManagement.earners}</div>
                  <p className="text-neutral-600">Earners</p>
                </div>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <div className="text-center">
                  <div className="text-3xl font-bold text-warning-600 mb-2">{userManagement.suspendedUsers}</div>
                  <p className="text-neutral-600">Suspended</p>
                </div>
              </CardBody>
            </Card>
            <Card>
              <CardBody>
                <div className="text-center">
                  <div className="text-3xl font-bold text-info-600 mb-2">{userManagement.pendingKYC}</div>
                  <p className="text-neutral-600">Pending KYC</p>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 mb-4">Recent Activity</h2>
          <Card>
            <CardBody>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      activity.severity === 'low' ? 'bg-neutral-100' :
                      activity.severity === 'medium' ? 'bg-warning-100' :
                      'bg-error-100'
                    }`}>
                      <span className={`text-sm ${
                        activity.severity === 'low' ? 'text-neutral-600' :
                        activity.severity === 'medium' ? 'text-warning-600' :
                        'text-error-600'
                      }`}>
                        {activity.type === 'user_registration' ? '👤' :
                         activity.type === 'campaign_created' ? '📊' :
                         activity.type === 'job_completed' ? '✅' :
                         activity.type === 'payment_processed' ? '💰' :
                         activity.type === 'flag_created' ? '🚩' :
                         '⚙️'}
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-neutral-900">{activity.description}</p>
                      <p className="text-sm text-neutral-600">
                        {new Date(activity.timestamp).toLocaleString()}
                        {activity.user && ` • User: ${activity.user}`}
                      </p>
                    </div>
                    <span className={`badge ${getSeverityColor(activity.severity)}`}>
                      {activity.severity.charAt(0).toUpperCase() + activity.severity.slice(1)}
                    </span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>

        {/* System Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">System Performance</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">API Response Time</span>
                  <span className="font-medium text-success-600">45ms</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Database Performance</span>
                  <span className="font-medium text-success-600">98%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">ML Service Status</span>
                  <span className="font-medium text-success-600">Online</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Payment Gateway</span>
                  <span className="font-medium text-success-600">Connected</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Security Status</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Failed Login Attempts</span>
                  <span className="font-medium text-warning-600">12</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Blocked IPs</span>
                  <span className="font-medium text-error-600">3</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Security Alerts</span>
                  <span className="font-medium text-warning-600">2</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-neutral-600">Last Security Scan</span>
                  <span className="font-medium text-success-600">2 hours ago</span>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
