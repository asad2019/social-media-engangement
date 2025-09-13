import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../../components/ui/Button';
import Card, { CardBody, CardHeader } from '../../../components/ui/Card';
import Tabs, { Tab } from '../../../components/ui/Tabs';

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
  endDate?: string;
}

interface Analytics {
  totalCampaigns: number;
  activeCampaigns: number;
  totalSpent: number;
  totalEngagements: number;
  conversionRate: number;
  avgCostPerEngagement: number;
  thisMonthSpent: number;
  pendingJobs: number;
}

const PromoterDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<Analytics>({
    totalCampaigns: 12,
    activeCampaigns: 3,
    totalSpent: 2450.75,
    totalEngagements: 15420,
    conversionRate: 87.5,
    avgCostPerEngagement: 0.16,
    thisMonthSpent: 320.25,
    pendingJobs: 8
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
      createdAt: '2024-01-15',
      endDate: '2024-02-15'
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
      createdAt: '2024-01-20',
      endDate: '2024-02-20'
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
      createdAt: '2024-01-10',
      endDate: '2024-02-10'
    }
  ]);

  const [quickActions] = useState([
    {
      title: 'Create New Campaign',
      description: 'Launch a new engagement campaign',
      icon: '🚀',
      link: '/promoter/campaigns/create',
      color: 'bg-primary-500'
    },
    {
      title: 'View Analytics',
      description: 'Check campaign performance',
      icon: '📊',
      link: '/promoter/analytics',
      color: 'bg-secondary-500'
    },
    {
      title: 'Manage Budget',
      description: 'Add funds to your account',
      icon: '💰',
      link: '/promoter/billing',
      color: 'bg-accent-500'
    },
    {
      title: 'Social Accounts',
      description: 'Manage your social media accounts',
      icon: '📱',
      link: '/promoter/social-accounts',
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

  const tabs: Tab[] = [
    {
      id: 'overview',
      label: 'Overview',
      content: (
        <div className="space-y-6">
          {/* Analytics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-neutral-600">Total Campaigns</p>
                    <p className="text-2xl font-bold text-neutral-900">{analytics.totalCampaigns}</p>
                    <p className="text-xs text-success-600">+{analytics.activeCampaigns} active</p>
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
                    <p className="text-xs text-neutral-500">{analytics.pendingJobs} pending jobs</p>
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
                    <p className="text-xs text-warning-600">${analytics.thisMonthSpent} this month</p>
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
                    <p className="text-xs text-success-600">{analytics.conversionRate}% conversion</p>
                  </div>
                  <div className="w-12 h-12 bg-info-100 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">👥</span>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Quick Actions */}
          <div>
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
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-neutral-900">Recent Campaigns</h2>
              <Link to="/promoter/campaigns">
                <Button variant="secondary" size="sm">View All</Button>
              </Link>
            </div>
            <Card>
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
                              <Link to={`/promoter/campaigns/${campaign.id}`}>
                                <Button size="sm" variant="secondary">View</Button>
                              </Link>
                              <Link to={`/promoter/campaigns/${campaign.id}/edit`}>
                                <Button size="sm">Edit</Button>
                              </Link>
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
        </div>
      )
    },
    {
      id: 'campaigns',
      label: 'Campaigns',
      content: (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-neutral-900">All Campaigns</h2>
            <Link to="/promoter/campaigns/create">
              <Button>Create Campaign</Button>
            </Link>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((campaign) => (
              <Card key={campaign.id} hover>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getPlatformIcon(campaign.platform)}</span>
                      <span className="font-semibold text-neutral-900">{campaign.platform}</span>
                    </div>
                    <span className={`badge ${getStatusColor(campaign.status)}`}>
                      {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-900 mt-2">{campaign.title}</h3>
                </CardHeader>
                <CardBody>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600">Budget:</span>
                      <span className="text-sm font-medium">${campaign.budget}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600">Spent:</span>
                      <span className="text-sm font-medium">${campaign.spent.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600">Engagements:</span>
                      <span className="text-sm font-medium">{campaign.engagements} / {campaign.targetEngagements}</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full" 
                        style={{ width: `${(campaign.engagements / campaign.targetEngagements) * 100}%` }}
                      ></div>
                    </div>
                    <div className="flex space-x-2 pt-2">
                      <Link to={`/promoter/campaigns/${campaign.id}`} className="flex-1">
                        <Button size="sm" variant="secondary" fullWidth>View Details</Button>
                      </Link>
                      <Link to={`/promoter/campaigns/${campaign.id}/edit`} className="flex-1">
                        <Button size="sm" fullWidth>Edit</Button>
                      </Link>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>
      )
    },
    {
      id: 'analytics',
      label: 'Analytics',
      content: (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-neutral-900">Campaign Analytics</h2>
          
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

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Spending Overview</h3>
            </CardHeader>
            <CardBody>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-neutral-900">${analytics.totalSpent.toLocaleString()}</div>
                  <p className="text-sm text-neutral-600">Total Spent</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-warning-600">${analytics.thisMonthSpent}</div>
                  <p className="text-sm text-neutral-600">This Month</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success-600">{analytics.totalEngagements.toLocaleString()}</div>
                  <p className="text-sm text-neutral-600">Total Engagements</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      )
    }
  ];

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
              <Link to="/promoter/campaigns/create">
                <Button>Create Campaign</Button>
              </Link>
              <Link to="/promoter/analytics">
                <Button variant="secondary">View Analytics</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs tabs={tabs} defaultTab="overview" />
      </div>
    </div>
  );
};

export default PromoterDashboard;
