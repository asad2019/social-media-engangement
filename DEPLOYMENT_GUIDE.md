# 🚀 Complete Deployment Guide

This comprehensive guide will walk you through setting up the Engagement Platform locally and deploying it to production. No prior experience with Docker, Kubernetes, or CI/CD is required.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Payment Integration](#payment-integration)
6. [Production Deployment](#production-deployment)
7. [CI/CD Setup](#cicd-setup)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software

1. **Docker & Docker Compose**
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Install and start Docker Desktop
   - Verify installation: `docker --version` and `docker-compose --version`

2. **Git**
   - [Download Git](https://git-scm.com/downloads)
   - Verify installation: `git --version`

3. **Node.js (for local development)**
   - [Download Node.js 18+](https://nodejs.org/)
   - Verify installation: `node --version` and `npm --version`

4. **Python 3.11+ (for local development)**
   - [Download Python](https://www.python.org/downloads/)
   - Verify installation: `python --version`

### Required Accounts & Services

1. **Stripe Account** (for payments)
   - Sign up at [stripe.com](https://stripe.com)
   - Get your API keys from the dashboard

2. **Domain Name** (for production)
   - Purchase a domain name
   - Configure DNS settings

3. **Cloud Provider Account** (for production)
   - AWS, Google Cloud, or Azure account
   - Or use Vercel for simpler deployment

---

## 🏠 Local Development Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <your-repository-url>
cd engagement-platform

# Verify the project structure
ls -la
```

### Step 2: Environment Configuration

1. **Copy the environment template:**
```bash
cp env.example .env
```

2. **Edit the `.env` file with your local settings:**
```bash
# Open the file in your preferred editor
nano .env
# or
code .env
```

3. **Configure the following variables:**

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
POSTGRES_DB=engagement_platform
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/engagement_platform

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=redis123

# MinIO/S3 Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=engagement-platform

# Stripe Configuration (Get these from your Stripe dashboard)
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret_here

# Service URLs
ML_SERVICE_URL=http://localhost:8001
TRACKER_SERVICE_URL=http://localhost:8002

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ML_SERVICE_URL=http://localhost:8001

# Platform Settings
PLATFORM_COMMISSION_RATE=0.05
KYC_THRESHOLD=100.00
MIN_WITHDRAWAL_AMOUNT=10.00
MAX_WITHDRAWAL_AMOUNT=10000.00
```

### Step 3: Start the Development Environment

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Start the development environment
./deploy.sh staging up
```

This command will:
- Build all Docker images
- Start all services (PostgreSQL, Redis, MinIO, Backend, Frontend, ML Service)
- Run database migrations
- Create a superuser account

### Step 4: Access the Application

After the setup completes, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/
- **ML Service**: http://localhost:8001
- **MinIO Console**: http://localhost:9001

### Step 5: Default Login Credentials

- **Superuser**: admin / admin123
- **MinIO**: minioadmin / minioadmin123

---

## 🗄️ Database Setup

### PostgreSQL Configuration

The platform uses PostgreSQL as the primary database. The Docker setup automatically creates and configures the database.

### Manual Database Setup (if needed)

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# Create database
CREATE DATABASE engagement_platform;

# Create user (if needed)
CREATE USER engagement_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE engagement_platform TO engagement_user;
```

### Database Migrations

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load sample data (optional)
docker-compose exec backend python manage.py loaddata sample_data.json
```

---

## 💳 Payment Integration

### Stripe Setup

1. **Create a Stripe Account:**
   - Go to [stripe.com](https://stripe.com)
   - Sign up for an account
   - Complete the account setup

2. **Get API Keys:**
   - Go to Developers > API Keys
   - Copy the Publishable Key and Secret Key
   - Add them to your `.env` file

3. **Set up Webhooks:**
   - Go to Developers > Webhooks
   - Add endpoint: `http://localhost:8000/api/v1/payments/webhook/`
   - Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
   - Copy the webhook secret to your `.env` file

4. **Test Payments:**
   - Use Stripe's test card numbers
   - Test successful payments: `4242 4242 4242 4242`
   - Test failed payments: `4000 0000 0000 0002`

### Stripe Connect Setup (for Earners)

1. **Enable Stripe Connect:**
   - Go to Connect in your Stripe dashboard
   - Enable Express accounts
   - Configure your platform settings

2. **Test Connected Accounts:**
   - Use Stripe's test mode
   - Create test connected accounts
   - Test payouts to connected accounts

---

## 🌐 Production Deployment

### Option 1: Vercel Deployment (Recommended for Beginners)

Vercel provides an easy way to deploy the frontend and backend.

#### Frontend Deployment

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Deploy Frontend:**
```bash
cd frontend
vercel --prod
```

3. **Configure Environment Variables:**
   - Go to your Vercel dashboard
   - Add environment variables:
     - `REACT_APP_API_URL=https://your-backend-domain.com/api/v1`
     - `REACT_APP_ML_SERVICE_URL=https://your-ml-service-domain.com`

#### Backend Deployment

1. **Deploy Backend:**
```bash
cd backend
vercel --prod
```

2. **Configure Environment Variables:**
   - Add all backend environment variables
   - Set `DEBUG=False`
   - Use production database URL
   - Use production Stripe keys

### Option 2: Docker Deployment

#### Using Docker Compose

1. **Prepare Production Environment:**
```bash
# Copy production environment file
cp env.example .env.prod

# Edit production settings
nano .env.prod
```

2. **Configure Production Environment:**
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@your-db-host:5432/engagement_platform
REDIS_URL=redis://your-redis-host:6379/0
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_stripe_key
STRIPE_SECRET_KEY=sk_live_your_live_stripe_key
```

3. **Deploy with Docker Compose:**
```bash
# Deploy to production
./deploy.sh production up
```

#### Using Kubernetes

1. **Set up Kubernetes Cluster:**
   - Use managed Kubernetes (EKS, GKE, AKS)
   - Or set up your own cluster

2. **Configure Secrets:**
```bash
# Create Kubernetes secrets
kubectl create secret generic engagement-platform-secrets \
  --from-literal=SECRET_KEY=your-secret-key \
  --from-literal=POSTGRES_PASSWORD=your-db-password \
  --from-literal=STRIPE_SECRET_KEY=your-stripe-key
```

3. **Deploy to Kubernetes:**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/production/

# Check deployment status
kubectl get pods
kubectl get services
```

### Option 3: Traditional Server Deployment

#### Ubuntu Server Setup

1. **Set up Server:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Deploy Application:**
```bash
# Clone repository
git clone <your-repository-url>
cd engagement-platform

# Configure environment
cp env.example .env
nano .env

# Deploy
./deploy.sh production up
```

3. **Set up Reverse Proxy (Nginx):**
```bash
# Install Nginx
sudo apt install nginx -y

# Configure Nginx
sudo nano /etc/nginx/sites-available/engagement-platform
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **Enable SSL with Let's Encrypt:**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com
```

---

## 🔄 CI/CD Setup

### GitHub Actions Setup

1. **Create GitHub Repository:**
   - Create a new repository on GitHub
   - Push your code to the repository

2. **Configure Secrets:**
   - Go to Settings > Secrets and variables > Actions
   - Add the following secrets:
     - `DOCKER_USERNAME`: Your Docker Hub username
     - `DOCKER_PASSWORD`: Your Docker Hub password
     - `STRIPE_SECRET_KEY`: Your Stripe secret key
     - `DATABASE_URL`: Your production database URL
     - `REDIS_URL`: Your production Redis URL

3. **Set up Workflows:**
   - The CI/CD workflow is already configured in `.github/workflows/ci.yml`
   - It will automatically run tests and deploy on push to main branch

### Manual CI/CD Setup

1. **Set up Staging Environment:**
```bash
# Deploy to staging
./deploy.sh staging up

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

2. **Set up Production Deployment:**
```bash
# Deploy to production
./deploy.sh production up

# Verify deployment
curl https://yourdomain.com/api/v1/health/
```

---

## 📊 Monitoring & Maintenance

### Health Checks

1. **Application Health:**
```bash
# Check backend health
curl http://localhost:8000/api/v1/health/

# Check frontend
curl http://localhost:3000

# Check ML service
curl http://localhost:8001/health
```

2. **Database Health:**
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready

# Check Redis
docker-compose exec redis redis-cli ping
```

### Monitoring Setup

1. **Prometheus & Grafana:**
```bash
# Start monitoring stack
docker-compose -f docker-compose.prod.yml up -d prometheus grafana

# Access Grafana
open http://localhost:3001
# Default login: admin / admin
```

2. **Log Management:**
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ml-service

# Log rotation
docker system prune -f
```

### Backup Strategy

1. **Database Backups:**
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres engagement_platform > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres engagement_platform < backup.sql
```

2. **Automated Backups:**
```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Docker Issues

**Problem**: Docker not starting
```bash
# Solution: Restart Docker service
sudo systemctl restart docker
```

**Problem**: Port already in use
```bash
# Solution: Find and kill process using port
sudo lsof -i :8000
sudo kill -9 <PID>
```

#### 2. Database Issues

**Problem**: Database connection failed
```bash
# Solution: Check database status
docker-compose exec postgres pg_isready

# Restart database
docker-compose restart postgres
```

**Problem**: Migration errors
```bash
# Solution: Reset migrations
docker-compose exec backend python manage.py migrate --fake-initial
```

#### 3. Frontend Issues

**Problem**: Build failures
```bash
# Solution: Clear cache and rebuild
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 4. Payment Issues

**Problem**: Stripe webhook failures
```bash
# Solution: Check webhook configuration
# Verify webhook URL and events
# Check webhook secret in environment variables
```

### Performance Optimization

1. **Database Optimization:**
```bash
# Add database indexes
docker-compose exec backend python manage.py dbshell
CREATE INDEX idx_job_status ON jobs_job(status);
CREATE INDEX idx_campaign_status ON campaigns_campaign(status);
```

2. **Caching Setup:**
```bash
# Configure Redis caching
# Add to Django settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

3. **Static Files:**
```bash
# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Serve with CDN
# Configure AWS CloudFront or similar
```

### Security Hardening

1. **Environment Security:**
```bash
# Use strong passwords
# Enable SSL/TLS
# Set up firewall rules
# Regular security updates
```

2. **Application Security:**
```bash
# Enable HTTPS
# Set security headers
# Regular dependency updates
# Security scanning
```

---

## 📞 Support & Resources

### Getting Help

1. **Documentation:**
   - Check the README.md file
   - Review API documentation at `/api/schema/swagger-ui/`

2. **Community:**
   - GitHub Issues for bug reports
   - Stack Overflow for questions
   - Discord/Slack community (if available)

3. **Professional Support:**
   - Contact support@engagement-platform.com
   - Hire a DevOps consultant for complex deployments

### Useful Commands

```bash
# View all running containers
docker ps

# View container logs
docker logs <container_name>

# Restart specific service
docker-compose restart <service_name>

# Scale services
docker-compose up -d --scale celery-worker=3

# Update application
git pull origin main
docker-compose build
docker-compose up -d
```

### Maintenance Checklist

- [ ] Regular database backups
- [ ] Security updates
- [ ] Performance monitoring
- [ ] Log rotation
- [ ] SSL certificate renewal
- [ ] Dependency updates
- [ ] User feedback review

---

## 🎉 Congratulations!

You've successfully set up the Engagement Platform! The system is now ready to:

- ✅ Handle user registrations and authentication
- ✅ Process campaign creation and funding
- ✅ Manage job assignments and completions
- ✅ Process payments and withdrawals
- ✅ Provide comprehensive admin controls
- ✅ Monitor system health and performance

### Next Steps

1. **Test the Platform:**
   - Create test accounts
   - Test campaign creation
   - Test job completion flow
   - Test payment processing

2. **Customize for Your Needs:**
   - Modify UI/UX
   - Adjust commission rates
   - Configure verification rules
   - Set up custom analytics

3. **Launch:**
   - Set up production environment
   - Configure monitoring
   - Train support team
   - Launch marketing campaign

### Need More Help?

If you encounter any issues or need assistance with deployment, please:

1. Check the troubleshooting section above
2. Review the GitHub issues
3. Contact our support team
4. Consider hiring a DevOps professional for complex deployments

**Happy Deploying! 🚀**
