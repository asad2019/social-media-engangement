import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  BriefcaseIcon,
  MegaphoneIcon,
} from '@heroicons/react/24/outline'

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  const stats = [
    {
      name: 'Wallet Balance',
      value: `$${user?.wallet_balance?.toFixed(2) || '0.00'}`,
      icon: CurrencyDollarIcon,
      color: 'text-success-600',
    },
    {
      name: 'Reputation Score',
      value: user?.reputation_score?.toFixed(1) || '0.0',
      icon: ChartBarIcon,
      color: 'text-primary-600',
    },
    {
      name: 'Active Jobs',
      value: '0',
      icon: BriefcaseIcon,
      color: 'text-warning-600',
    },
    {
      name: 'Campaigns',
      value: '0',
      icon: MegaphoneIcon,
      color: 'text-secondary-600',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here's what's happening with your account today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="card">
              <div className="card-body">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Icon className={`h-8 w-8 ${stat.color}`} />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        {stat.name}
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {stat.value}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              {user?.role === 'promoter' && (
                <>
                  <button className="w-full btn-primary text-left">
                    Create New Campaign
                  </button>
                  <button className="w-full btn-secondary text-left">
                    View Campaign Analytics
                  </button>
                </>
              )}
              {user?.role === 'earner' && (
                <>
                  <button className="w-full btn-primary text-left">
                    Browse Available Jobs
                  </button>
                  <button className="w-full btn-secondary text-left">
                    View Job History
                  </button>
                </>
              )}
              <button className="w-full btn-secondary text-left">
                Manage Social Accounts
              </button>
              <button className="w-full btn-secondary text-left">
                Update Profile
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="card-body">
            <div className="text-center text-gray-500 py-8">
              <p>No recent activity</p>
              <p className="text-sm mt-1">Your activity will appear here</p>
            </div>
          </div>
        </div>
      </div>

      {/* Account Status */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Account Status</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm font-medium text-gray-500">KYC Status</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">
                {user?.kyc_status?.replace('_', ' ')}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Account Verified</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {user?.is_verified ? 'Yes' : 'No'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Role</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">
                {user?.role}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Member Since</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </dd>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
