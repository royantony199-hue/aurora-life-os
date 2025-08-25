#!/bin/bash
# Aurora Life OS Deployment Script

set -e

# Configuration
PROJECT_NAME="aurora-life-os"
DOCKER_COMPOSE_FILE="docker-compose.yml"
PRODUCTION_COMPOSE_FILE="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

show_usage() {
    echo "Aurora Life OS Deployment Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  dev         - Start development environment"
    echo "  prod        - Start production environment"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs        - Show logs"
    echo "  backup      - Create database backup"
    echo "  restore     - Restore database from backup"
    echo "  migrate     - Run database migrations"
    echo "  setup       - Initial setup (copy .env, install dependencies)"
    echo "  clean       - Clean up containers and volumes"
    echo "  status      - Show service status"
    echo ""
    echo "Options:"
    echo "  --build     - Force rebuild containers"
    echo "  --no-cache  - Build without cache"
    echo ""
    exit 1
}

check_requirements() {
    log "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if running from correct directory
    if [[ ! -f "docker-compose.yml" ]]; then
        error "Please run this script from the project root directory."
    fi
    
    success "Requirements check passed"
}

setup_environment() {
    log "Setting up environment..."
    
    # Copy .env.example if .env doesn't exist
    if [[ ! -f "backend/.env" ]]; then
        if [[ -f "backend/.env.example" ]]; then
            cp "backend/.env.example" "backend/.env"
            warning "Created backend/.env from .env.example. Please update with your values."
        else
            error "No .env.example file found in backend directory"
        fi
    fi
    
    # Create necessary directories
    mkdir -p database/backups database/init logs ssl
    
    # Set permissions for scripts
    chmod +x scripts/*.sh scripts/*.py 2>/dev/null || true
    
    success "Environment setup complete"
}

start_development() {
    log "Starting development environment..."
    
    local build_flag=""
    if [[ "$1" == "--build" ]]; then
        build_flag="--build"
    fi
    
    docker-compose -f ${DOCKER_COMPOSE_FILE} up -d ${build_flag}
    
    # Wait for services to be healthy
    log "Waiting for services to start..."
    sleep 10
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose -f ${DOCKER_COMPOSE_FILE} exec backend alembic upgrade head || warning "Migration failed - database might not be ready"
    
    success "Development environment started!"
    log "🌐 Frontend: http://localhost:5173"
    log "🔧 Backend API: http://localhost:8001"
    log "📊 API Docs: http://localhost:8001/docs"
    log "🐘 PostgreSQL: localhost:5432"
    log "🔴 Redis: localhost:6379"
}

start_production() {
    log "Starting production environment..."
    
    # Check if production .env exists
    if [[ ! -f "backend/.env" ]]; then
        error "Production .env file not found. Run 'setup' first."
    fi
    
    # Verify required environment variables
    source backend/.env
    if [[ -z "$SECRET_KEY" || -z "$DATABASE_URL" ]]; then
        error "Required environment variables not set. Check your .env file."
    fi
    
    local build_flag=""
    if [[ "$1" == "--build" ]]; then
        build_flag="--build"
    fi
    
    docker-compose -f ${PRODUCTION_COMPOSE_FILE} up -d ${build_flag}
    
    # Wait for services
    log "Waiting for production services to start..."
    sleep 15
    
    # Run migrations
    log "Running database migrations..."
    docker-compose -f ${PRODUCTION_COMPOSE_FILE} exec backend alembic upgrade head
    
    success "Production environment started!"
    log "🌐 Application: http://localhost"
    log "🔧 Backend API: http://localhost/api"
}

stop_services() {
    log "Stopping services..."
    
    docker-compose -f ${DOCKER_COMPOSE_FILE} down 2>/dev/null || true
    docker-compose -f ${PRODUCTION_COMPOSE_FILE} down 2>/dev/null || true
    
    success "Services stopped"
}

restart_services() {
    log "Restarting services..."
    stop_services
    sleep 2
    
    if [[ -f "${PRODUCTION_COMPOSE_FILE}" ]] && docker-compose -f ${PRODUCTION_COMPOSE_FILE} ps | grep -q "Up"; then
        start_production "$@"
    else
        start_development "$@"
    fi
}

show_logs() {
    log "Showing logs..."
    
    local service="${2:-}"
    if [[ -n "$service" ]]; then
        docker-compose -f ${DOCKER_COMPOSE_FILE} logs -f "$service"
    else
        docker-compose -f ${DOCKER_COMPOSE_FILE} logs -f
    fi
}

create_backup() {
    log "Creating database backup..."
    
    # Check if backup service is available
    if docker-compose -f ${DOCKER_COMPOSE_FILE} ps postgres | grep -q "Up"; then
        docker-compose -f ${DOCKER_COMPOSE_FILE} exec postgres \
            bash -c 'pg_dump -U $POSTGRES_USER -d $POSTGRES_DB | gzip > /backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz'
        success "Database backup created"
    else
        error "PostgreSQL service is not running"
    fi
}

restore_backup() {
    local backup_file="$2"
    if [[ -z "$backup_file" ]]; then
        error "Please specify backup file: $0 restore <backup_file>"
    fi
    
    log "Restoring database from $backup_file..."
    
    if [[ ! -f "database/backups/$backup_file" ]]; then
        error "Backup file not found: database/backups/$backup_file"
    fi
    
    warning "This will replace all current data. Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Restore cancelled"
        exit 0
    fi
    
    docker-compose -f ${DOCKER_COMPOSE_FILE} exec postgres \
        bash -c "gunzip -c /backups/$backup_file | psql -U \$POSTGRES_USER -d \$POSTGRES_DB"
    
    success "Database restored from $backup_file"
}

run_migrations() {
    log "Running database migrations..."
    
    if docker-compose -f ${DOCKER_COMPOSE_FILE} ps backend | grep -q "Up"; then
        docker-compose -f ${DOCKER_COMPOSE_FILE} exec backend alembic upgrade head
        success "Migrations completed"
    else
        error "Backend service is not running"
    fi
}

clean_up() {
    log "Cleaning up containers and volumes..."
    
    warning "This will remove all containers, images, and volumes. Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Cleanup cancelled"
        exit 0
    fi
    
    stop_services
    
    # Remove containers
    docker-compose -f ${DOCKER_COMPOSE_FILE} rm -f 2>/dev/null || true
    docker-compose -f ${PRODUCTION_COMPOSE_FILE} rm -f 2>/dev/null || true
    
    # Remove volumes
    docker volume prune -f
    
    # Remove images
    docker image prune -f
    
    success "Cleanup completed"
}

show_status() {
    log "Service status:"
    echo ""
    
    echo "Development services:"
    docker-compose -f ${DOCKER_COMPOSE_FILE} ps 2>/dev/null || echo "Not running"
    
    echo ""
    echo "Production services:"
    docker-compose -f ${PRODUCTION_COMPOSE_FILE} ps 2>/dev/null || echo "Not running"
    
    echo ""
    log "Docker system info:"
    docker system df
}

# Main script
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
    fi
    
    check_requirements
    
    case "$1" in
        "dev")
            shift
            start_development "$@"
            ;;
        "prod")
            shift
            start_production "$@"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            shift
            restart_services "$@"
            ;;
        "logs")
            shift
            show_logs "$@"
            ;;
        "backup")
            create_backup
            ;;
        "restore")
            shift
            restore_backup "$@"
            ;;
        "migrate")
            run_migrations
            ;;
        "setup")
            setup_environment
            ;;
        "clean")
            clean_up
            ;;
        "status")
            show_status
            ;;
        *)
            show_usage
            ;;
    esac
}

main "$@"