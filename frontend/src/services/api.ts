import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`
          originalRequest.headers['Authorization'] = `Bearer ${access}`

          return api(originalRequest)
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        delete api.defaults.headers.common['Authorization']
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  login: (credentials: { username: string; password: string }) =>
    api.post('/auth/login/', credentials),
  register: (userData: any) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
  profile: () => api.get('/auth/profile/'),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh/', { refresh: refreshToken }),
}

export const campaignsAPI = {
  list: (params?: any) => api.get('/campaigns/', { params }),
  create: (data: any) => api.post('/campaigns/', data),
  get: (id: string) => api.get(`/campaigns/${id}/`),
  update: (id: string, data: any) => api.put(`/campaigns/${id}/`, data),
  delete: (id: string) => api.delete(`/campaigns/${id}/`),
  fund: (id: string, data: any) => api.post(`/campaigns/${id}/fund/`, data),
  pause: (id: string) => api.post(`/campaigns/${id}/pause/`),
  resume: (id: string) => api.post(`/campaigns/${id}/resume/`),
  cancel: (id: string) => api.post(`/campaigns/${id}/cancel/`),
  preview: (data: any) => api.post('/campaigns/preview/', data),
}

export const jobsAPI = {
  feed: (params?: any) => api.get('/jobs/feed/', { params }),
  accept: (id: string) => api.post(`/jobs/${id}/accept/`),
  submit: (id: string, data: any) => api.post(`/jobs/${id}/submit/`, data),
  cancel: (id: string) => api.post(`/jobs/${id}/cancel/`),
  search: (params: any) => api.get('/jobs/feed/search/', { params }),
  filter: (params: any) => api.get('/jobs/feed/filter/', { params }),
  recommended: () => api.get('/jobs/feed/recommended/'),
  stats: () => api.get('/jobs/stats/'),
  userStats: () => api.get('/jobs/stats/user/'),
}

export const walletAPI = {
  balance: () => api.get('/wallets/balance/'),
  overview: () => api.get('/wallets/overview/'),
  transactions: (params?: any) => api.get('/wallets/transactions/', { params }),
  withdraw: (data: any) => api.post('/wallets/withdraw/', data),
  cancelWithdrawal: (id: string) => api.post(`/wallets/withdrawals/${id}/cancel/`),
  exportTransactions: () => api.get('/wallets/transactions/export/'),
  summary: () => api.get('/wallets/transactions/summary/'),
}

export const socialAccountsAPI = {
  list: () => api.get('/auth/social-accounts/'),
  create: (data: any) => api.post('/auth/social-accounts/', data),
  update: (id: string, data: any) => api.put(`/auth/social-accounts/${id}/`, data),
  delete: (id: string) => api.delete(`/auth/social-accounts/${id}/`),
  verify: (id: string) => api.post(`/auth/social-accounts/${id}/verify/`),
}

export const adminAPI = {
  dashboard: () => api.get('/admin/dashboard/'),
  metrics: () => api.get('/admin/dashboard/metrics/'),
  alerts: () => api.get('/admin/dashboard/alerts/'),
  users: (params?: any) => api.get('/admin/users/', { params }),
  campaigns: (params?: any) => api.get('/admin/campaigns/', { params }),
  jobs: (params?: any) => api.get('/admin/jobs/', { params }),
  withdrawals: (params?: any) => api.get('/admin/withdrawals/', { params }),
  suspendUser: (id: string, data: any) => api.post(`/admin/users/${id}/suspend/`, data),
  banUser: (id: string, data: any) => api.post(`/admin/users/${id}/ban/`, data),
  verifyUser: (id: string) => api.post(`/admin/users/${id}/verify/`),
  adjustWallet: (id: string, data: any) => api.post(`/admin/users/${id}/wallet-adjust/`, data),
  approveWithdrawal: (id: string) => api.post(`/admin/withdrawals/${id}/approve/`),
  rejectWithdrawal: (id: string, data: any) => api.post(`/admin/withdrawals/${id}/reject/`, data),
  approveJob: (id: string) => api.post(`/admin/jobs/${id}/approve/`),
  rejectJob: (id: string, data: any) => api.post(`/admin/jobs/${id}/reject/`, data),
}
