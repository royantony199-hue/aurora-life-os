-- Initialize Aurora Life OS Database
-- This script sets up the database with proper configurations

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create database user if it doesn't exist (for manual setup)
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'aurora_user') THEN
      CREATE ROLE aurora_user LOGIN PASSWORD 'aurora_pass';
   END IF;
END
$do$;

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE aurora_db TO aurora_user;
GRANT ALL ON SCHEMA public TO aurora_user;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create indexes for common queries (will be created after tables via Alembic)
-- These are just placeholders for documentation

-- Performance settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'none';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Memory settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Connection settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET max_prepared_transactions = 0;

SELECT pg_reload_conf();

-- Log initialization
INSERT INTO public.system_log (message, timestamp) 
VALUES ('Aurora Life OS database initialized', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;