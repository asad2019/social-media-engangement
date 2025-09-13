import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/ui/Button';
import Card, { CardBody, CardHeader } from '../components/ui/Card';

interface Job {
  id: string;
  title: string;
  platform: string;
  reward: number;
  status: 'available' | 'accepted' | 'completed' | 'verified' | 'rejected';
  description: string;
  requirements: string[];
  createdAt: string;
  deadline?: string;
}

interface Earnings {
  totalEarned: number;
  pendingEarnings: number;
  completedJobs: number;
  successRate: number;
  avgEarningPerJob: number;
  thisMonthEarnings: number;
}

interface SocialAccount {
  id: string;
  platform: string;
  username: string;
  followers: number;
  verified: boolean;
  score: number;
}

const EarnerDashboard: React.FC = () => {
  const [earnings, setEarnings] = useState<Earnings>({
    totalEarned: 1250.75,
    pendingEarnings: 85.50,
    completedJobs: 45,
    successRate: 92.5,
    avgEarningPerJob: 27.79,
    thisMonthEarnings: 320.25
  });

  const [availableJobs, setAvailableJobs] = useState<Job[]>([
    {
      id: '1',
      title: 'Instagram Fashion Post Like',
      platform: 'Instagram',
      reward: 0.15,
      status: 'available',
      description: 'Like and engage with our latest fashion post',
      requirements: ['Active Instagram account', 'Minimum 100 followers', 'Real engagement'],
      createdAt: '2024-01-20',
      deadline: '2024-01-25'
    },
    {
      id: '2',
      title: 'Twitter Tech Thread Comment',
      platform: 'Twitter',
      reward: 0.25,
      status: 'available',
      description: 'Comment thoughtfully on our tech thread',
      requirements: ['Active Twitter account', 'Tech interest', 'Quality comments'],
      createdAt: '2024-01-20',
      deadline: '2024-01-24'
    },
    {
      id: '3',
      title: 'TikTok Dance Video Follow',
      platform: 'TikTok',
      reward: 0.20,
      status: 'available',
      description: 'Follow our TikTok account and engage with dance content',
      requirements: ['Active TikTok account', 'Dance content interest'],
      createdAt: '2024-01-19',
      deadline: '2024-01-23'
    }
  ]);

  const [myJobs, setMyJobs] = useState<Job[]>([
    {
      id: '4',
      title: 'YouTube Tech Review Subscribe',
      platform: 'YouTube',
      reward: 0.50,
      status: 'verified',
      description: 'Subscribe to our tech channel and watch latest review',
      requirements: ['Active YouTube account', 'Tech interest'],
      createdAt: '2024-01-18'
    },
    {
      id: '5',
      title: 'LinkedIn Business Post Share',
      platform: 'LinkedIn',
      reward: 0.35,
      status: 'completed',
      description: 'Share our business insights post',
      requirements: ['Professional LinkedIn profile'],
      createdAt: '2024-01-17'
    }
  ]);

  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([
    {
      id: '1',
      platform: 'Instagram',
      username: '@fashionista_2024',
      followers: 1250,
      verified: true,
      score: 85
    },
    {
      id: '2',
      platform: 'Twitter',
      username: '@techlover99',
      followers: 850,
      verified: true,
      score: 78
    },
    {
      id: '3',
      platform: 'TikTok',
      username: '@dancequeen',
      followers: 2100,
      verified: false,
      score: 92
    }
  ]);

  const [quickActions] = useState([
    {
      title: 'Browse Available Jobs',
      description: 'Find new earning opportunities',
      icon: '🔍',
      link: '/jobs',
      color: 'bg-primary-500'
    },
    {
      title: 'My Earnings',
      description: 'Track your income and payouts',
      icon: '💰',
      link: '/earnings',
      color: 'bg-success-500'
    },
    {
      title: 'Social Accounts',
      description: 'Manage your connected accounts',
      icon: '📱',
      link: '/accounts',
      color: 'bg-secondary-500'
    },
    {
      title: 'Withdraw Funds',
      description: 'Cash out your earnings',
      icon: '💳',
      link: '/withdraw',
      color: 'bg-accent-500'
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'badge-primary';
      case 'accepted': return 'badge-warning';
      case 'completed': return 'badge-info';
      case 'verified': return 'badge-success';
      case 'rejected': return 'badge-error';
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

  const getVerificationBadge = (verified: boolean) => {
    return verified ? (
      <span className="badge badge-success">Verified</span>
    ) : (
      <span className="badge badge-warning">Pending</span>
    );
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Earner Dashboard</h1>
              <p className="text-neutral-600">Find jobs, track earnings, and grow your income</p>
            </div>
            <div className="flex space-x-3">
              <Link to="/jobs">
                <Button>Browse Jobs</Button>
              </Link>
              <Button variant="secondary">View Earnings</Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Earnings Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Total Earned</p>
                  <p className="text-2xl font-bold text-success-600">${earnings.totalEarned.toFixed(2)}</p>
                </div>
                <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">💰</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Pending Earnings</p>
                  <p className="text-2xl font-bold text-warning-600">${earnings.pendingEarnings.toFixed(2)}</p>
                </div>
                <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">⏳</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Completed Jobs</p>
                  <p className="text-2xl font-bold text-primary-600">{earnings.completedJobs}</p>
                </div>
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">✅</span>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-neutral-600">Success Rate</p>
                  <p className="text-2xl font-bold text-info-600">{earnings.successRate}%</p>
                </div>
                <div className="w-12 h-12 bg-info-100 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📈</span>
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

        {/* Available Jobs */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-neutral-900">Available Jobs</h2>
            <Link to="/jobs">
              <Button variant="secondary" size="sm">View All</Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableJobs.map((job) => (
              <Card key={job.id} hover className="cursor-pointer">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{getPlatformIcon(job.platform)}</span>
                      <span className="font-semibold text-neutral-900">{job.platform}</span>
                    </div>
                    <span className={`badge ${getStatusColor(job.status)}`}>
                      {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-neutral-900 mt-2">{job.title}</h3>
                </CardHeader>
                <CardBody>
                  <p className="text-neutral-600 mb-4">{job.description}</p>
                  <div className="mb-4">
                    <h4 className="font-medium text-neutral-900 mb-2">Requirements:</h4>
                    <ul className="text-sm text-neutral-600 space-y-1">
                      {job.requirements.map((req, index) => (
                        <li key={index}>• {req}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-2xl font-bold text-success-600">${job.reward.toFixed(2)}</div>
                    <Button size="sm">Accept Job</Button>
                  </div>
                  {job.deadline && (
                    <div className="mt-2 text-sm text-neutral-500">
                      Deadline: {new Date(job.deadline).toLocaleDateString()}
                    </div>
                  )}
                </CardBody>
              </Card>
            ))}
          </div>
        </div>

        {/* My Jobs */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-neutral-900">My Jobs</h2>
            <Link to="/my-jobs">
              <Button variant="secondary" size="sm">View All</Button>
            </Link>
          </div>
          <Card>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="table w-full">
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Platform</th>
                      <th>Status</th>
                      <th>Reward</th>
                      <th>Completed</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myJobs.map((job) => (
                      <tr key={job.id}>
                        <td>
                          <div>
                            <div className="font-medium text-neutral-900">{job.title}</div>
                            <div className="text-sm text-neutral-500">Started {new Date(job.createdAt).toLocaleDateString()}</div>
                          </div>
                        </td>
                        <td>
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{getPlatformIcon(job.platform)}</span>
                            <span className="text-sm">{job.platform}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${getStatusColor(job.status)}`}>
                            {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                          </span>
                        </td>
                        <td>
                          <div className="font-medium text-success-600">${job.reward.toFixed(2)}</div>
                        </td>
                        <td>
                          <div className="text-sm text-neutral-600">
                            {job.status === 'verified' ? 'Yes' : 'Pending'}
                          </div>
                        </td>
                        <td>
                          <div className="flex space-x-2">
                            <Button size="sm" variant="secondary">View</Button>
                            {job.status === 'completed' && (
                              <Button size="sm">Submit Proof</Button>
                            )}
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

        {/* Social Accounts */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-neutral-900">Connected Accounts</h2>
            <Link to="/accounts">
              <Button variant="secondary" size="sm">Manage</Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {socialAccounts.map((account) => (
              <Card key={account.id}>
                <CardBody>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getPlatformIcon(account.platform)}</span>
                      <div>
                        <h3 className="font-semibold text-neutral-900">{account.platform}</h3>
                        <p className="text-sm text-neutral-600">{account.username}</p>
                      </div>
                    </div>
                    {getVerificationBadge(account.verified)}
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600">Followers:</span>
                      <span className="text-sm font-medium">{account.followers.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-neutral-600">Account Score:</span>
                      <span className="text-sm font-medium">{account.score}/100</span>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div 
                        className="bg-primary-600 h-2 rounded-full" 
                        style={{ width: `${account.score}%` }}
                      ></div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Earnings This Month</h3>
            </CardHeader>
            <CardBody>
              <div className="text-center">
                <div className="text-4xl font-bold text-success-600 mb-2">${earnings.thisMonthEarnings.toFixed(2)}</div>
                <p className="text-neutral-600">Total earnings this month</p>
                <div className="mt-4 text-sm text-neutral-500">
                  <span className="text-success-600">↑ 15%</span> from last month
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-semibold text-neutral-900">Average Per Job</h3>
            </CardHeader>
            <CardBody>
              <div className="text-center">
                <div className="text-4xl font-bold text-primary-600 mb-2">${earnings.avgEarningPerJob.toFixed(2)}</div>
                <p className="text-neutral-600">Average earning per completed job</p>
                <div className="mt-4 text-sm text-neutral-500">
                  Based on {earnings.completedJobs} completed jobs
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
                    <span className="text-success-600">💰</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">Earned $0.50 from YouTube Tech Review Subscribe</p>
                    <p className="text-sm text-neutral-600">1 hour ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-primary-600">✅</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">Job "LinkedIn Business Post Share" completed</p>
                    <p className="text-sm text-neutral-600">3 hours ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4 p-4 bg-neutral-50 rounded-lg">
                  <div className="w-10 h-10 bg-info-100 rounded-full flex items-center justify-center">
                    <span className="text-info-600">📱</span>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-neutral-900">TikTok account verified successfully</p>
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

export default EarnerDashboard;
