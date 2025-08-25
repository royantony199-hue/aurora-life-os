#!/bin/bash
# Automated PostgreSQL Backup Script for Aurora Life OS

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-aurora_db}"
DB_USER="${POSTGRES_USER:-aurora_user}"
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/aurora_backup_${TIMESTAMP}.sql"

# Ensure backup directory exists
mkdir -p ${BACKUP_DIR}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🚀 Starting PostgreSQL backup..."
log "📊 Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log "💾 Backup file: ${BACKUP_FILE}"

# Create backup
log "⏳ Creating backup..."
if pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    --verbose --clean --if-exists --create --format=plain > ${BACKUP_FILE} 2>/dev/null; then
    
    # Compress backup
    log "🗜️  Compressing backup..."
    gzip ${BACKUP_FILE}
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    
    # Verify backup
    if [ -f "${COMPRESSED_FILE}" ] && [ -s "${COMPRESSED_FILE}" ]; then
        BACKUP_SIZE=$(du -h "${COMPRESSED_FILE}" | cut -f1)
        log "✅ Backup completed successfully!"
        log "📏 Backup size: ${BACKUP_SIZE}"
        
        # Create metadata file
        cat > "${COMPRESSED_FILE}.info" << EOF
Backup Information
==================
Database: ${DB_NAME}
Host: ${DB_HOST}:${DB_PORT}
User: ${DB_USER}
Timestamp: ${TIMESTAMP}
File: $(basename ${COMPRESSED_FILE})
Size: ${BACKUP_SIZE}
Created: $(date)
EOF
        
        log "📋 Metadata created: ${COMPRESSED_FILE}.info"
    else
        log "❌ Backup verification failed!"
        exit 1
    fi
else
    log "❌ Backup creation failed!"
    exit 1
fi

# Cleanup old backups
log "🗑️  Cleaning up backups older than ${RETENTION_DAYS} days..."
find ${BACKUP_DIR} -name "aurora_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "aurora_backup_*.sql.gz.info" -type f -mtime +${RETENTION_DAYS} -delete

# List current backups
log "📂 Current backups:"
ls -lah ${BACKUP_DIR}/aurora_backup_*.sql.gz 2>/dev/null | tail -5 || log "No backups found"

log "🎉 Backup process completed!"

# Optional: Upload to cloud storage (uncomment and configure as needed)
# if [ ! -z "${AWS_S3_BUCKET}" ]; then
#     log "☁️  Uploading to S3..."
#     aws s3 cp ${COMPRESSED_FILE} s3://${AWS_S3_BUCKET}/database-backups/
#     aws s3 cp ${COMPRESSED_FILE}.info s3://${AWS_S3_BUCKET}/database-backups/
#     log "✅ S3 upload completed"
# fi