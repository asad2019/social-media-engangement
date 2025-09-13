import React from 'react'

export const WalletPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Wallet</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage your earnings and withdrawals
        </p>
      </div>
      
      <div className="card">
        <div className="card-body text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">Wallet Coming Soon</h3>
          <p className="mt-2 text-gray-600">
            This feature is under development and will be available soon.
          </p>
        </div>
      </div>
    </div>
  )
}
