#!/bin/bash

# Engagement Platform Deployment Script
# Usage: ./deploy.sh [staging|production] [up|down|restart]

set -e

ENVIRONMENT=${1:-staging}
ACTION=${2:-up}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        log_warn ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log_warn "Please update .env file with your actual values before proceeding."
        else
            log_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
    
    log_info "Prerequisites check completed."
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend
    log_info "Building backend image..."
    docker build -t engagement-platform-backend:latest ./backend
    
    # Build frontend
    log_info "Building frontend image..."
    docker build -t engagement-platform-frontend:latest ./frontend
    
    # Build ML service
    log_info "Building ML service image..."
    docker build -t engagement-platform-ml:latest ./ml-service
    
    log_info "All images built successfully."
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Run migrations
    docker-compose exec backend python manage.py migrate
    
    # Create superuser if it doesn't exist
    log_info "Creating superuser..."
    docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
    
    log_info "Database setup completed."
}

deploy_staging() {
    log_info "Deploying to staging environment..."
    
    # Use docker-compose.yml for staging
    COMPOSE_FILE="docker-compose.yml"
    
    case $ACTION in
        "up")
            check_prerequisites
            build_images
            log_info "Starting staging environment..."
            docker-compose -f $COMPOSE_FILE up -d
            run_migrations
            log_info "Staging environment is up and running!"
            log_info "Frontend: http://localhost:3000"
            log_info "Backend API: http://localhost:8000"
            log_info "ML Service: http://localhost:8001"
            ;;
        "down")
            log_info "Stopping staging environment..."
            docker-compose -f $COMPOSE_FILE down
            log_info "Staging environment stopped."
            ;;
        "restart")
            log_info "Restarting staging environment..."
            docker-compose -f $COMPOSE_FILE down
            docker-compose -f $COMPOSE_FILE up -d
            run_migrations
            log_info "Staging environment restarted."
            ;;
        *)
            log_error "Invalid action: $ACTION. Use 'up', 'down', or 'restart'."
            exit 1
            ;;
    esac
}

deploy_production() {
    log_info "Deploying to production environment..."
    
    # Use docker-compose.prod.yml for production
    COMPOSE_FILE="docker-compose.prod.yml"
    
    case $ACTION in
        "up")
            check_prerequisites
            build_images
            log_info "Starting production environment..."
            docker-compose -f $COMPOSE_FILE up -d
            run_migrations
            log_info "Production environment is up and running!"
            ;;
        "down")
            log_info "Stopping production environment..."
            docker-compose -f $COMPOSE_FILE down
            log_info "Production environment stopped."
            ;;
        "restart")
            log_info "Restarting production environment..."
            docker-compose -f $COMPOSE_FILE down
            docker-compose -f $COMPOSE_FILE up -d
            run_migrations
            log_info "Production environment restarted."
            ;;
        *)
            log_error "Invalid action: $ACTION. Use 'up', 'down', or 'restart'."
            exit 1
            ;;
    esac
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    NAMESPACE="engagement-platform-${ENVIRONMENT}"
    
    case $ACTION in
        "up")
            log_info "Applying Kubernetes manifests..."
            kubectl apply -f k8s/${ENVIRONMENT}/
            log_info "Waiting for deployments to be ready..."
            kubectl wait --for=condition=available --timeout=300s deployment --all -n $NAMESPACE
            log_info "Kubernetes deployment completed!"
            ;;
        "down")
            log_info "Removing Kubernetes resources..."
            kubectl delete -f k8s/${ENVIRONMENT}/
            log_info "Kubernetes resources removed."
            ;;
        *)
            log_error "Invalid action: $ACTION. Use 'up' or 'down'."
            exit 1
            ;;
    esac
}

show_help() {
    echo "Engagement Platform Deployment Script"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [ACTION]"
    echo ""
    echo "ENVIRONMENTS:"
    echo "  staging     Deploy to staging environment (default)"
    echo "  production  Deploy to production environment"
    echo "  k8s         Deploy to Kubernetes"
    echo ""
    echo "ACTIONS:"
    echo "  up          Start the environment (default)"
    echo "  down        Stop the environment"
    echo "  restart     Restart the environment"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 staging up          # Start staging environment"
    echo "  $0 production restart  # Restart production environment"
    echo "  $0 k8s up              # Deploy to Kubernetes"
    echo ""
}

# Main script logic
case $ENVIRONMENT in
    "staging")
        deploy_staging
        ;;
    "production")
        deploy_production
        ;;
    "k8s")
        deploy_kubernetes
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        show_help
        exit 1
        ;;
esac

log_info "Deployment script completed successfully!"
