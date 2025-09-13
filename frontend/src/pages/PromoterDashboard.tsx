import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card, { CardBody, CardHeader } from '../components/ui/Card';
import Input from '../components/ui/Input';

interface Campaign {
  id: string;
  title: string;
  platform: string;
  status: 'active' | 'paused' | 'completed' | 'draft';
  budget: number;
  spent: number;
  engagements: number;
  targetEngagements: number;
  createdAt: string;
}

interface Analytics {
  totalCampaigns: number;
  activeCampaigns: number;
  totalSpent: number;
  totalEngagements: number;
  conversionRate: number;
  avgCostPerEngagement: number;
}

const PromoterDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<Analytics>({
    totalCampaigns: 12,
    activeCampaigns: 3,
    totalSpent: 2450.75,
    totalEngagements: 15420,
    conversionRate: 87.5,
    avgCostPerEngagement: 0.16
  });

  const [campaigns, setCampaigns] = useState<Campaign[]>([
    {
      id: '1',
      title: 'Instagram Fashion Campaign',
      platform: 'Instagram',
      status: 'active',
      budget: 500,
      spent: 320.50,
      engagements: 2100,
      targetEngagements: 3000,
      createdAt: '2024-01-15'
    },
    {
      id: '2',
      title: 'Twitter Tech Launch',
      platform: 'Twitter',
      status: 'active',
      budget: 300,
      spent: 180.25,
      engagements: 1200,
      targetEngagements: 1500,
      createdAt: '2024-01-20'
    },
    {
      id: '3',
      title: 'TikTok Dance Challenge',
      platform: 'TikTok',
      status: 'paused',
      budget: 800,
      spent: 450.00,
      engagements: 3200,
      targetEngagements: 5000,
      createdAt: '2024-01-10'
    }
  ]);

  const [quickActions] = useState([
    {
      title: 'Create New Campaign',
      description: 'Launch a new engagement campaign',
      icon: '🚀',
      link: '/campaigns/create',
      color: 'bg-primary-500'
    },
    {
      title: 'View Analytics',
      description: 'Check campaign performance',
      icon: '📊',
      link: '/analytics',
      color: 'bg-secondary-500'
    },
    {
      title: 'Manage Budget',
      description: 'Add funds to your account',
      icon: '💰',
      link: '/wallet',
      color: 'bg-accent-500'
    },
    {
      title: 'Support Center',
      description: 'Get help and support',
      icon: '🎧',
      link: '/support',
      color: 'bg-info-500'
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'badge-success';
      case 'paused': return 'badge-warning';
      case 'completed': return 'badge-primary';
      case 'draft': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'Instagram': return '📷';
      case 'Twitter': return '🐦';
      case 'Facebook': return '📘';
      case 'TikTok': return '🎵';
      case 'YouTube': return '📺';
      case 'LinkedIn': return '💼';
      default: return '📱';
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Promoter Dashboard</h1>
              <p className="text-neutral-600">Manage your campaigns and track performance</p>
            </div>
            <div className="flex space-x-3">
              <Link to="/campaigns/create">
                <Button>Create Campaign</Button>
              </Link>
              <Button variant="secondary">View Analytics</Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Analytics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Campaigns</p>
                  <p className="text-2xl font-bold text-neutral-900">{analytics.totalCampaigns}</p>
                </div>
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📈</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Active Campaigns</p>
                  <p className="text-2xl font-bold text-success-600">{analytics.activeCampaigns}</p>
                </div>
                <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">🎯</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Spent</p>
                  <p className="text-2xl font-bold text-neutral-900">${analytics.totalSpent.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">💰</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Engagements</p>
                  <p className="text-2xl font-bold text-neutral-900">{analytics.totalEngagements.toLocaleString()}</p>
                </div>
                <div className="w-12 h-12 bg-info-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">👥</span>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

        {/* Recent Campaigns */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-neutral-900">Recent Campaigns</h2>
            <Link to="/campaigns">
              <Button variant="secondary" size="sm">View All</Button>
            </Link>
          </div>
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Campaign Overview</h3>
            </CardHeader>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="table w-full">
                  <thead>
                    <tr>
                      <th>Campaign</th>
                      <th>Platform</th>
                      <th>Status</th>
                      <th>Budget</th>
                      <th>Spent</th>
                      <th>Progress</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaigns.map((campaign) => (
                      <tr key={campaign.id}>
                        <td>
                          <div>
                            <div className="font-medium text-neutral-900">{campaign.title}</div>
                            <div className="text-sm text-neutral-500">Created {new Date(campaign.createdAt).toLocaleDateString()}</div>
                          </div>
                        </td>
                        <td>
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{getPlatformIcon(campaign.platform)}</span>
                            <span className="text-sm">{campaign.platform}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${getStatusColor(campaign.status)}`}>
                            {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                          </span>
                        </td>
                        <td>
                          <div className="font-medium">${campaign.budget}</div>
                        </td>
                        <td>
                          <div className="font-medium">${campaign.spent.toFixed(2)}</div>
                        </td>
                        <td>
                          <div className="w-full bg-neutral-200 rounded-full h-2">
                            <div 
                              className="bg-primary-600 h-2 rounded-full" 
                              style={{ width: `${(campaign.engagements / campaign.targetEngagements) * 100}%` }}
                            ></div>
                          </div>
                          <div className="text-sm text-neutral-600 mt-1">
                            {campaign.engagements} / {campaign.targetEngagements}
                          </div>
                        </td>
                        <td>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="secondary">View</Button>
                            <Button size="sm">Edit</Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Conversion Rate</h3>
            </CardHeader>
            <CardBody>
              <div className="text-center">
                <div className="text-4xl font-bold text-success-600 mb-2">{analytics.conversionRate}%</div>
                <p className="text-neutral-600">Average conversion rate across all campaigns</p>
                <div className="mt-4">
                  <div className="w-full bg-neutral-200 rounded-full h-3">
                    <div 
                      className="bg-success-600 h-3 rounded-full" 
                      style={{ width: `${analytics.conversionRate}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Cost Per Engagement</h3>
            </CardHeader>
            <CardBody>
              <div className="text-center">
                <div className="text-4xl font-bold text-primary-600 mb-2">${analytics.avgCostPerEngagement}</div>
                <p className="text-neutral-600">Average cost per engagement</p>
                <div className="mt-4 text-sm text-neutral-500">
                  <span className="text-success-600">↓ 12%</span> from last month
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-neutral-900 mb-4">Recent Activity</h2>
          <Card>
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                  <div className="w-10 h-10 bg-success-100 rounded-full flex items-center justify-center">
                    <span className="text-success-600">✓</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">Campaign "Instagram Fashion Campaign" completed</p>
                    <p className="text-sm text-neutral-600">2 hours ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-600">💰</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">Payment of $150.00 processed</p>
                    <p className="text-sm text-neutral-600">4 hours ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                  <div className="w-10 h-10 bg-warning-100 rounded-full flex items-center justify-center">
                    <span className="text-warning-600">⚠️</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">Campaign "TikTok Dance Challenge" paused</p>
                    <p className="text-sm text-neutral-600">1 day ago</p>
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PromoterDashboard;
