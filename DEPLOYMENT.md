# Aurora Life OS - Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL client (optional, for manual database operations)
- 4GB+ RAM recommended
- 10GB+ disk space

### 1. Initial Setup
```bash
# Clone and navigate to project
cd aurora-life-os

# Setup environment and dependencies
./scripts/deploy.sh setup
```

### 2. Configure Environment
```bash
# Edit the environment file
nano backend/.env

# Required variables:
SECRET_KEY="your-super-secure-secret-key-here"
REFRESH_SECRET_KEY="your-refresh-secret-key-here"
ENCRYPTION_KEY="your-32-character-encryption-key"
DATABASE_URL="postgresql://aurora_user:aurora_pass@postgres:5432/aurora_db"
```

### 3. Deploy

**Development:**
```bash
./scripts/deploy.sh dev
```

**Production:**
```bash
./scripts/deploy.sh prod
```

## 🔧 Environment Configuration

### Required Environment Variables

```env
# Application
APP_NAME="Aurora Life OS"
VERSION="1.0.0"
ENVIRONMENT="production"  # development, staging, production
DEBUG="false"

# Security - MUST BE CHANGED FOR PRODUCTION
SECRET_KEY="your-jwt-secret-key-32-chars-minimum"
REFRESH_SECRET_KEY="your-refresh-token-secret-key"
ENCRYPTION_KEY="exactly-32-characters-for-fernet"

# Database
DATABASE_URL="postgresql://user:password@host:5432/database"
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Security Settings
API_RATE_LIMIT_PER_MINUTE=100
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# CORS (production domains only)
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"

# External APIs
OPENAI_API_KEY="your-openai-api-key"
GOOGLE_CLIENT_ID="your-google-oauth-client-id"
GOOGLE_CLIENT_SECRET="your-google-oauth-secret"

# Redis
REDIS_URL="redis://redis:6379/0"
REDIS_PASSWORD=""  # Set for production

# Monitoring
LOG_LEVEL="INFO"
SENTRY_DSN=""  # Optional error tracking

# SSL/HTTPS
FORCE_HTTPS="true"  # Enable in production
```

### Generate Secure Keys

```bash
# Generate secure keys
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('REFRESH_SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(24)[:32])"
```

## 🐳 Docker Architecture

### Services Overview

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| **postgres** | PostgreSQL 15 database | 5432 | `pg_isready` |
| **redis** | Redis cache & session store | 6379 | `redis-cli ping` |
| **backend** | FastAPI Python backend | 8000 | `/health` endpoint |
| **frontend** | React TypeScript app | 5173/80 | HTTP response |
| **nginx** | Reverse proxy (prod only) | 80/443 | HTTP response |

### Development vs Production

**Development (`docker-compose.yml`):**
- Hot reload enabled
- Debug logging
- Direct port access
- SQLite fallback support
- Development CORS origins

**Production (`docker-compose.prod.yml`):**
- Optimized builds
- Multi-stage containers
- Nginx reverse proxy
- SSL/HTTPS ready
- Security headers
- Production logging
- Rate limiting

## 📊 Database Management

### Migration from SQLite to PostgreSQL

If you have existing SQLite data:

```bash
# 1. Start PostgreSQL service
./scripts/deploy.sh dev

# 2. Run migration script
docker-compose exec backend python scripts/migrate_to_postgresql.py

# 3. Verify migration
docker-compose exec backend python -c "
from app.core.database import check_database_connection, get_database_info
print('Connection:', check_database_connection())
print('Database:', get_database_info())
"
```

### Database Operations

```bash
# Run migrations
./scripts/deploy.sh migrate

# Create backup
./scripts/deploy.sh backup

# Restore from backup
./scripts/deploy.sh restore backup_20231220_143022.sql.gz

# Manual database access
docker-compose exec postgres psql -U aurora_user -d aurora_db

# View database logs
docker-compose logs postgres
```

### Automated Backups

Backups are automated with the backup service:

```bash
# Start backup service
docker-compose exec backend python scripts/backup_service.py service

# Manual backup types
docker-compose exec backend python scripts/backup_service.py database
docker-compose exec backend python scripts/backup_service.py application
docker-compose exec backend python scripts/backup_service.py full
```

**Backup Schedule:**
- Daily database backup: 2:00 AM
- Daily application backup: 1:00 AM  
- Weekly full backup: Sunday 3:00 AM
- Daily cleanup: 4:00 AM

## 🔒 Security Features

### Implemented Security Measures

✅ **Authentication & Authorization:**
- JWT tokens with refresh mechanism
- Password complexity requirements
- Account lockout protection
- Rate limiting on login attempts

✅ **API Security:**
- Rate limiting middleware
- Request validation
- SQL injection protection
- XSS protection headers

✅ **Data Protection:**
- Sensitive data encryption
- Secure password hashing (bcrypt)
- Database connection pooling
- Environment variable protection

✅ **Infrastructure Security:**
- Security headers middleware
- CORS policy enforcement
- Content Security Policy (CSP)
- Docker container isolation

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Set strong SECRET_KEY and ENCRYPTION_KEY
- [ ] Configure HTTPS/SSL certificates
- [ ] Set production CORS origins
- [ ] Enable security headers
- [ ] Configure firewall rules
- [ ] Set up monitoring/alerting
- [ ] Regular security updates
- [ ] Database access restrictions
- [ ] Backup encryption

## 🚀 Deployment Commands

### Basic Operations
```bash
# Start development environment
./scripts/deploy.sh dev

# Start production environment  
./scripts/deploy.sh prod

# Stop all services
./scripts/deploy.sh stop

# Restart services
./scripts/deploy.sh restart

# View logs
./scripts/deploy.sh logs
./scripts/deploy.sh logs backend  # specific service

# Check service status
./scripts/deploy.sh status
```

### Advanced Operations
```bash
# Force rebuild containers
./scripts/deploy.sh dev --build
./scripts/deploy.sh prod --build --no-cache

# Database operations
./scripts/deploy.sh migrate
./scripts/deploy.sh backup
./scripts/deploy.sh restore backup_file.sql.gz

# Cleanup
./scripts/deploy.sh clean
```

## 🔍 Monitoring & Troubleshooting

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health  
docker-compose exec postgres pg_isready -U aurora_user

# Redis health
docker-compose exec redis redis-cli ping

# Service status
docker-compose ps
```

### Log Analysis

```bash
# Application logs
docker-compose logs backend -f

# Database logs
docker-compose logs postgres -f

# All services
docker-compose logs -f

# System resource usage
docker stats
```

### Common Issues

**Database Connection Issues:**
```bash
# Check database status
docker-compose exec postgres pg_isready -U aurora_user -d aurora_db

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

**Memory Issues:**
```bash
# Check container memory usage
docker stats

# Restart services with limited memory
docker-compose down && docker-compose up -d
```

**Permission Issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh scripts/*.py
```

## 🌐 Production Deployment

### Recommended Infrastructure

**Minimum Requirements:**
- 2 CPU cores
- 4GB RAM
- 20GB SSD storage
- Ubuntu 20.04+ or similar

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ SSD storage
- Load balancer
- Monitoring solution

### SSL/HTTPS Setup

1. **Obtain SSL Certificate:**
```bash
# Using Certbot (Let's Encrypt)
sudo certbot certonly --nginx -d yourdomain.com
```

2. **Configure Nginx:**
```bash
# Update nginx/nginx.conf with SSL configuration
# Copy certificate files to ssl/ directory
```

3. **Enable HTTPS:**
```bash
# Update .env
FORCE_HTTPS=true
ALLOWED_ORIGINS=https://yourdomain.com

# Restart services
./scripts/deploy.sh restart prod
```

### Performance Optimization

**Database Optimization:**
```bash
# Update PostgreSQL settings in docker-compose.prod.yml
# Increase connection pools for high traffic
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
```

**Redis Configuration:**
```bash
# Enable Redis persistence
# Configure memory limits
# Set up Redis clustering for scale
```

**Application Scaling:**
```bash
# Increase backend workers
# Update docker-compose.prod.yml:
command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

## 📈 Maintenance

### Regular Tasks

**Daily:**
- Monitor system resources
- Check application logs
- Verify backup completion

**Weekly:**
- Update dependencies
- Security patch review  
- Performance analysis

**Monthly:**
- Full system backup
- Security audit
- Capacity planning

### Update Procedure

```bash
# 1. Backup current state
./scripts/deploy.sh backup

# 2. Pull latest changes
git pull origin main

# 3. Rebuild containers
./scripts/deploy.sh prod --build

# 4. Run migrations
./scripts/deploy.sh migrate

# 5. Verify deployment
./scripts/deploy.sh status
```

## 🆘 Disaster Recovery

### Backup Strategy

**Automated Backups:**
- Database: Daily at 2 AM
- Application data: Daily at 1 AM
- Full system: Weekly on Sunday

**Backup Locations:**
- Local: `database/backups/`
- Optional: AWS S3, Google Cloud Storage

### Recovery Procedures

**Database Recovery:**
```bash
# 1. Stop services
./scripts/deploy.sh stop

# 2. Restore database
./scripts/deploy.sh restore latest_backup.sql.gz

# 3. Start services
./scripts/deploy.sh prod
```

**Full System Recovery:**
```bash
# 1. Fresh deployment
./scripts/deploy.sh setup
./scripts/deploy.sh prod --build

# 2. Restore data
./scripts/deploy.sh restore backup_file.sql.gz

# 3. Verify functionality
./scripts/deploy.sh status
```

---

## 🎯 Next Steps

After successful deployment:

1. **Configure monitoring** (Prometheus, Grafana)
2. **Set up CI/CD pipeline** (GitHub Actions)
3. **Configure log aggregation** (ELK stack)
4. **Implement automated testing**
5. **Set up staging environment**
6. **Configure alerting** (PagerDuty, Slack)

---

## 📞 Support

For deployment issues:
1. Check logs: `./scripts/deploy.sh logs`
2. Verify configuration: `./scripts/deploy.sh status`
3. Review this guide
4. Check Docker/system resources