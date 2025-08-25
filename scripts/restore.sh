#!/bin/bash
# Database Restoration Script for Aurora Life OS

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-aurora_db}"
DB_USER="${POSTGRES_USER:-aurora_user}"
BACKUP_DIR="/backups"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

show_usage() {
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -1 ${BACKUP_DIR}/aurora_backup_*.sql.gz 2>/dev/null | tail -10 || echo "No backups found"
    exit 1
}

# Check if backup file is provided
if [ $# -eq 0 ]; then
    show_usage
fi

BACKUP_FILE="$1"

# If only filename provided, prepend backup directory
if [[ "$BACKUP_FILE" != /* ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log "❌ Backup file not found: $BACKUP_FILE"
    show_usage
fi

log "🚀 Starting database restoration..."
log "📊 Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
log "📁 Backup file: $BACKUP_FILE"

# Check if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "🗜️  Decompressing backup..."
    TEMP_FILE="/tmp/restore_${RANDOM}.sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Show backup info if available
INFO_FILE="${BACKUP_FILE}.info"
if [ -f "$INFO_FILE" ]; then
    log "📋 Backup information:"
    cat "$INFO_FILE"
    echo ""
fi

# Confirm restoration
read -p "⚠️  This will REPLACE all data in database '${DB_NAME}'. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "❌ Restoration cancelled by user"
    [ -f "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
    exit 1
fi

# Create backup of current database before restoration
CURRENT_BACKUP="/tmp/current_backup_$(date +%Y%m%d_%H%M%S).sql"
log "💾 Creating backup of current database..."
pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} > "${CURRENT_BACKUP}" || {
    log "⚠️  Failed to backup current database, but continuing..."
}

# Restore database
log "⏳ Restoring database..."
if psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -f "${RESTORE_FILE}"; then
    log "✅ Database restoration completed successfully!"
    
    # Test connection
    log "🔍 Testing database connection..."
    if psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" > /dev/null 2>&1; then
        log "✅ Database connection test passed!"
    else
        log "⚠️  Database connection test failed!"
    fi
    
    # Show restored table count
    TABLE_COUNT=$(psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    log "📊 Restored ${TABLE_COUNT} tables"
    
else
    log "❌ Database restoration failed!"
    log "💾 Current database backup saved to: ${CURRENT_BACKUP}"
    [ -f "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
    exit 1
fi

# Cleanup
[ -f "$TEMP_FILE" ] && rm -f "$TEMP_FILE"
[ -f "$CURRENT_BACKUP" ] && rm -f "$CURRENT_BACKUP"

log "🎉 Restoration process completed!"
log "📝 Remember to restart your application to ensure all changes take effect"