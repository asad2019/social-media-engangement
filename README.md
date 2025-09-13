# Engagement Platform

A secure, auditable, and scalable marketplace where Promoters pay to create engagement tasks and Earners complete tasks for pay.

## 🚀 Features

- **Secure Marketplace**: Promoters create engagement tasks, Earners complete them for payment
- **Verification System**: Multi-layer verification (deterministic, ML, manual review)
- **Payment Integration**: Stripe Connect with ledger-first financial model
- **Admin Console**: Comprehensive moderation and management tools
- **ML Service**: Account scoring and fraud detection
- **Security & Compliance**: Audit logging, rate limiting, data encryption
- **Scalable Architecture**: Microservices with Docker and Kubernetes support

## 🏗️ Architecture

### Backend (Django + DRF)
- **Framework**: Django 4.2 with Django REST Framework
- **Database**: PostgreSQL with JSONB support
- **Cache**: Redis for caching and Celery broker
- **Storage**: MinIO/S3 for file storage
- **Authentication**: JWT with refresh tokens
- **API Documentation**: OpenAPI/Swagger with drf-spectacular

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **State Management**: React Context API
- **Routing**: React Router DOM

### ML Service (FastAPI)
- **Framework**: FastAPI
- **Features**: Account scoring, verification, comment analysis
- **Models**: TensorFlow/PyTorch for ML inference

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development, Kubernetes for production
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions
- **Security**: Rate limiting, audit logging, data encryption

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd engagement-platform
```

### 2. Environment Setup
```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Start Development Environment
```bash
./deploy.sh staging up
```

This will:
- Build all Docker images
- Start all services (PostgreSQL, Redis, MinIO, Backend, Frontend, ML Service)
- Run database migrations
- Create a superuser account

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/
- **ML Service**: http://localhost:8001
- **MinIO Console**: http://localhost:9001

### 5. Default Credentials
- **Superuser**: admin / admin123
- **MinIO**: minioadmin / minioadmin123

## 📖 Complete Setup Guide

For detailed setup instructions, environment configuration, and deployment guides, see:

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Complete deployment guide for local and production setup
- **[Environment Configuration](#environment-configuration)** - Required environment variables
- **[Payment Integration](#payment-integration)** - Stripe setup and configuration

## 🛠️ Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### ML Service Development
```bash
cd ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# ML Service tests
cd ml-service
pytest
```

## 🚀 Deployment

### Staging Deployment
```bash
./deploy.sh staging up
```

### Production Deployment
```bash
./deploy.sh production up
```

### Kubernetes Deployment
```bash
./deploy.sh k8s up
```

## 📊 Monitoring

### Prometheus Metrics
- **Backend**: http://localhost:8000/metrics
- **ML Service**: http://localhost:8001/metrics
- **Prometheus**: http://localhost:9090

### Grafana Dashboards
- **Grafana**: http://localhost:3001
- **Default credentials**: admin / admin

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
ML_SERVICE_URL=http://localhost:8001
TRACKER_SERVICE_URL=http://localhost:8002
```

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ML_SERVICE_URL=http://localhost:8001
```

## 📁 Project Structure

```
engagement-platform/
├── backend/                 # Django backend
│   ├── engagement_platform/ # Django project settings
│   ├── users/              # User management
│   ├── campaigns/          # Campaign management
│   ├── jobs/               # Job management
│   ├── wallets/            # Wallet and transactions
│   ├── verification/       # Verification system
│   ├── admin_console/      # Admin tools
│   ├── payments/           # Payment integration
│   └── security/           # Security features
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   └── services/       # API services
│   └── public/             # Static assets
├── ml-service/             # FastAPI ML service
│   ├── models/             # Pydantic models
│   ├── services/           # ML services
│   └── main.py            # FastAPI app
├── k8s/                    # Kubernetes manifests
│   ├── staging/            # Staging configs
│   └── production/         # Production configs
├── monitoring/             # Monitoring configs
│   ├── prometheus/         # Prometheus config
│   └── grafana/            # Grafana config
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
├── deploy.sh               # Deployment script
└── README.md               # This file
```

## 🔒 Security Features

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: Configurable rate limits per endpoint
- **Audit Logging**: Comprehensive audit trail
- **Data Encryption**: Encryption at rest and in transit
- **Input Validation**: Comprehensive input sanitization
- **Security Headers**: HSTS, XSS protection, CSRF protection

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Model and service tests
- **Integration Tests**: API endpoint tests
- **E2E Tests**: Frontend user journey tests
- **Security Tests**: Security vulnerability tests
- **Load Tests**: Performance and scalability tests

### Running Tests
```bash
# All tests
./scripts/run-tests.sh

# Backend only
cd backend && pytest

# Frontend only
cd frontend && npm test

# ML Service only
cd ml-service && pytest
```

## 📈 Performance

### Optimization Features
- **Database**: Query optimization, connection pooling
- **Caching**: Redis caching for frequently accessed data
- **CDN**: Static asset delivery optimization
- **Compression**: Gzip compression for API responses
- **Pagination**: Efficient data pagination
- **Background Tasks**: Celery for async processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@engagement-platform.com or join our Slack channel.

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced ML models
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] API rate limiting improvements
- [ ] Enhanced security features

## 🙏 Acknowledgments

- Django and Django REST Framework
- React and TypeScript communities
- FastAPI and Pydantic
- Docker and Kubernetes communities
- Stripe for payment processing
- All open-source contributors