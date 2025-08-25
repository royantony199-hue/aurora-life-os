#!/bin/bash
# Test Aurora Life OS deployment

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

test_requirement() {
    local cmd="$1"
    local name="$2"
    
    if command -v "$cmd" &> /dev/null; then
        log "$name is installed ✅"
        return 0
    else
        error "$name is not installed ❌"
        return 1
    fi
}

test_file_exists() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        log "$description exists ✅"
        return 0
    else
        error "$description not found: $file ❌"
        return 1
    fi
}

test_directory_exists() {
    local dir="$1"
    local description="$2"
    
    if [[ -d "$dir" ]]; then
        log "$description exists ✅"
        return 0
    else
        error "$description not found: $dir ❌"
        return 1
    fi
}

test_service_health() {
    local service="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    log "Testing $service health..."
    
    if curl -f -s --max-time "$timeout" "$url" > /dev/null; then
        log "$service is healthy ✅"
        return 0
    else
        error "$service is not responding ❌"
        return 1
    fi
}

run_tests() {
    log "🧪 Running Aurora Life OS deployment tests..."
    echo ""
    
    # Test 1: Requirements
    log "1️⃣ Testing requirements..."
    test_requirement "docker" "Docker"
    test_requirement "docker-compose" "Docker Compose"
    test_requirement "curl" "curl"
    echo ""
    
    # Test 2: Project structure
    log "2️⃣ Testing project structure..."
    test_file_exists "docker-compose.yml" "Development Docker Compose"
    test_file_exists "docker-compose.prod.yml" "Production Docker Compose"
    test_file_exists "backend/Dockerfile" "Backend Dockerfile"
    test_file_exists "frontend/Dockerfile" "Frontend Dockerfile"
    test_file_exists "scripts/deploy.sh" "Deploy script"
    test_directory_exists "backend" "Backend directory"
    test_directory_exists "frontend" "Frontend directory"
    test_directory_exists "database" "Database directory"
    echo ""
    
    # Test 3: Configuration files
    log "3️⃣ Testing configuration files..."
    test_file_exists "backend/.env.example" ".env example"
    test_file_exists "backend/requirements.txt" "Backend requirements"
    test_file_exists "frontend/package.json" "Frontend package.json"
    test_file_exists "backend/alembic.ini" "Alembic configuration"
    echo ""
    
    # Test 4: Scripts and permissions
    log "4️⃣ Testing scripts..."
    test_file_exists "scripts/deploy.sh" "Deploy script"
    test_file_exists "scripts/backup.sh" "Backup script"
    test_file_exists "scripts/restore.sh" "Restore script"
    test_file_exists "scripts/migrate_to_postgresql.py" "Migration script"
    
    # Check if scripts are executable
    if [[ -x "scripts/deploy.sh" ]]; then
        log "Deploy script is executable ✅"
    else
        warning "Deploy script is not executable. Run: chmod +x scripts/*.sh"
    fi
    echo ""
    
    # Test 5: Environment file
    log "5️⃣ Testing environment configuration..."
    if [[ -f "backend/.env" ]]; then
        log "Environment file exists ✅"
        
        # Check for required variables
        source backend/.env
        
        if [[ -n "$SECRET_KEY" && "$SECRET_KEY" != "your-secret-key-here" ]]; then
            log "SECRET_KEY is configured ✅"
        else
            warning "SECRET_KEY needs to be set"
        fi
        
        if [[ -n "$DATABASE_URL" ]]; then
            log "DATABASE_URL is configured ✅"
        else
            warning "DATABASE_URL needs to be set"
        fi
        
    else
        warning "Environment file not found. Run: ./scripts/deploy.sh setup"
    fi
    echo ""
    
    # Test 6: Docker services (if running)
    log "6️⃣ Testing Docker services..."
    
    if docker-compose ps | grep -q "Up"; then
        log "Docker services are running ✅"
        
        # Test individual services
        if docker-compose ps postgres | grep -q "Up"; then
            log "PostgreSQL service is running ✅"
        fi
        
        if docker-compose ps redis | grep -q "Up"; then
            log "Redis service is running ✅"
        fi
        
        if docker-compose ps backend | grep -q "Up"; then
            log "Backend service is running ✅"
            
            # Test backend health
            if curl -f -s --max-time 10 "http://localhost:8001/health" > /dev/null; then
                log "Backend health check passed ✅"
            else
                warning "Backend health check failed"
            fi
        fi
        
        if docker-compose ps frontend | grep -q "Up"; then
            log "Frontend service is running ✅"
        fi
        
    else
        warning "Docker services are not running. Start with: ./scripts/deploy.sh dev"
    fi
    echo ""
    
    # Test 7: API endpoints (if services are running)
    if docker-compose ps backend | grep -q "Up"; then
        log "7️⃣ Testing API endpoints..."
        
        # Test health endpoint
        if curl -f -s "http://localhost:8001/health" | grep -q "healthy"; then
            log "Health endpoint working ✅"
        else
            warning "Health endpoint not responding properly"
        fi
        
        # Test API docs
        if curl -f -s --max-time 5 "http://localhost:8001/docs" > /dev/null; then
            log "API documentation accessible ✅"
        else
            warning "API documentation not accessible"
        fi
        
        # Test CORS headers
        if curl -s -H "Origin: http://localhost:5173" "http://localhost:8001/health" -I | grep -q "Access-Control"; then
            log "CORS headers present ✅"
        else
            warning "CORS headers not found"
        fi
    else
        warning "Skipping API tests - backend not running"
    fi
    echo ""
    
    # Test 8: Database connectivity (if services are running)
    if docker-compose ps postgres | grep -q "Up"; then
        log "8️⃣ Testing database connectivity..."
        
        if docker-compose exec -T postgres pg_isready -U aurora_user > /dev/null 2>&1; then
            log "PostgreSQL is ready ✅"
        else
            warning "PostgreSQL is not ready"
        fi
        
        # Test database connection from backend
        if docker-compose ps backend | grep -q "Up"; then
            if docker-compose exec -T backend python -c "
from app.core.database import check_database_connection
result = check_database_connection()
print('Database connection:', 'OK' if result else 'FAILED')
exit(0 if result else 1)
" 2>/dev/null; then
                log "Backend database connection working ✅"
            else
                warning "Backend cannot connect to database"
            fi
        fi
    else
        warning "Skipping database tests - PostgreSQL not running"
    fi
    echo ""
    
    # Test 9: Security checks
    log "9️⃣ Testing security configuration..."
    
    if [[ -f "backend/.env" ]]; then
        source backend/.env
        
        # Check secret keys
        if [[ ${#SECRET_KEY} -ge 32 ]]; then
            log "SECRET_KEY length is adequate ✅"
        else
            warning "SECRET_KEY should be at least 32 characters"
        fi
        
        # Check CORS in production
        if [[ "$ENVIRONMENT" == "production" ]]; then
            if [[ "$ALLOWED_ORIGINS" != *"*"* ]]; then
                log "Production CORS properly configured ✅"
            else
                warning "Production CORS allows all origins (*)"
            fi
        fi
        
        # Check database URL
        if [[ "$DATABASE_URL" == postgresql* ]]; then
            log "Using PostgreSQL (recommended) ✅"
        else
            warning "Not using PostgreSQL database"
        fi
    fi
    echo ""
    
    # Test 10: Performance and resources
    log "🔟 Testing system resources..."
    
    # Check available disk space
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [[ $available_space -gt 5242880 ]]; then  # 5GB in KB
        log "Sufficient disk space available ✅"
    else
        warning "Low disk space (less than 5GB available)"
    fi
    
    # Check available memory
    if command -v free &> /dev/null; then
        available_memory=$(free -m | awk 'NR==2{print $7}')
        if [[ $available_memory -gt 1000 ]]; then  # 1GB
            log "Sufficient memory available ✅"
        else
            warning "Low available memory (less than 1GB)"
        fi
    fi
    
    echo ""
    log "🎉 Deployment test completed!"
    
    # Summary
    echo ""
    echo "📋 Summary:"
    echo "   - Run './scripts/deploy.sh dev' to start development"
    echo "   - Run './scripts/deploy.sh prod' to start production"
    echo "   - Check './scripts/deploy.sh status' for service status"
    echo "   - View logs with './scripts/deploy.sh logs'"
    echo ""
    echo "🌐 URLs (when running):"
    echo "   - Frontend: http://localhost:5173"
    echo "   - Backend API: http://localhost:8001"
    echo "   - API Docs: http://localhost:8001/docs"
    echo ""
}

# Run tests
run_tests