import React from 'react'

export const JobsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <p className="mt-1 text-sm text-gray-600">
          Browse and complete engagement tasks
        </p>
      </div>
      
      <div className="card">
        <div className="card-body text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">Jobs Coming Soon</h3>
          <p className="mt-2 text-gray-600">
            This feature is under development and will be available soon.
          </p>
        </div>
      </div>
    </div>
  )
}
