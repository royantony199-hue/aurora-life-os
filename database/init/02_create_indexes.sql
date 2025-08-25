-- Performance Indexes for Aurora Life OS
-- These indexes will be created after tables are set up via Alembic

-- Function to create indexes safely
CREATE OR REPLACE FUNCTION create_index_if_not_exists(index_name text, create_sql text)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = index_name) THEN
        EXECUTE create_sql;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Wait for tables to be created by the application
-- Then create performance indexes

DO $$
BEGIN
    -- Check if main tables exist before creating indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        
        -- User indexes
        PERFORM create_index_if_not_exists('idx_users_username', 
            'CREATE INDEX CONCURRENTLY idx_users_username ON users(username)');
        PERFORM create_index_if_not_exists('idx_users_email', 
            'CREATE INDEX CONCURRENTLY idx_users_email ON users(email)');
        PERFORM create_index_if_not_exists('idx_users_is_active', 
            'CREATE INDEX CONCURRENTLY idx_users_is_active ON users(is_active)');
        
        -- Goals indexes
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'goals') THEN
            PERFORM create_index_if_not_exists('idx_goals_user_id', 
                'CREATE INDEX CONCURRENTLY idx_goals_user_id ON goals(user_id)');
            PERFORM create_index_if_not_exists('idx_goals_status', 
                'CREATE INDEX CONCURRENTLY idx_goals_status ON goals(status)');
            PERFORM create_index_if_not_exists('idx_goals_target_date', 
                'CREATE INDEX CONCURRENTLY idx_goals_target_date ON goals(target_date)');
            PERFORM create_index_if_not_exists('idx_goals_user_status', 
                'CREATE INDEX CONCURRENTLY idx_goals_user_status ON goals(user_id, status)');
        END IF;
        
        -- Mood indexes
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'moods') THEN
            PERFORM create_index_if_not_exists('idx_moods_user_id', 
                'CREATE INDEX CONCURRENTLY idx_moods_user_id ON moods(user_id)');
            PERFORM create_index_if_not_exists('idx_moods_created_at', 
                'CREATE INDEX CONCURRENTLY idx_moods_created_at ON moods(created_at)');
            PERFORM create_index_if_not_exists('idx_moods_user_date', 
                'CREATE INDEX CONCURRENTLY idx_moods_user_date ON moods(user_id, created_at DESC)');
        END IF;
        
        -- Calendar events indexes
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'calendar_events') THEN
            PERFORM create_index_if_not_exists('idx_calendar_events_user_id', 
                'CREATE INDEX CONCURRENTLY idx_calendar_events_user_id ON calendar_events(user_id)');
            PERFORM create_index_if_not_exists('idx_calendar_events_start_time', 
                'CREATE INDEX CONCURRENTLY idx_calendar_events_start_time ON calendar_events(start_time)');
            PERFORM create_index_if_not_exists('idx_calendar_events_user_start', 
                'CREATE INDEX CONCURRENTLY idx_calendar_events_user_start ON calendar_events(user_id, start_time)');
            PERFORM create_index_if_not_exists('idx_calendar_events_google_id', 
                'CREATE INDEX CONCURRENTLY idx_calendar_events_google_id ON calendar_events(google_event_id) WHERE google_event_id IS NOT NULL');
        END IF;
        
        -- Chat messages indexes
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chats') THEN
            PERFORM create_index_if_not_exists('idx_chats_user_id', 
                'CREATE INDEX CONCURRENTLY idx_chats_user_id ON chats(user_id)');
            PERFORM create_index_if_not_exists('idx_chats_timestamp', 
                'CREATE INDEX CONCURRENTLY idx_chats_timestamp ON chats(timestamp)');
            PERFORM create_index_if_not_exists('idx_chats_user_timestamp', 
                'CREATE INDEX CONCURRENTLY idx_chats_user_timestamp ON chats(user_id, timestamp DESC)');
        END IF;
        
        -- Tasks indexes (if table exists)
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
            PERFORM create_index_if_not_exists('idx_tasks_user_id', 
                'CREATE INDEX CONCURRENTLY idx_tasks_user_id ON tasks(user_id)');
            PERFORM create_index_if_not_exists('idx_tasks_status', 
                'CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status)');
            PERFORM create_index_if_not_exists('idx_tasks_due_date', 
                'CREATE INDEX CONCURRENTLY idx_tasks_due_date ON tasks(due_date)');
            PERFORM create_index_if_not_exists('idx_tasks_user_status', 
                'CREATE INDEX CONCURRENTLY idx_tasks_user_status ON tasks(user_id, status)');
        END IF;
        
    END IF;
END $$;

-- Function to analyze tables for better query planning
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS void AS $$
BEGIN
    ANALYZE users;
    ANALYZE goals;
    ANALYZE moods; 
    ANALYZE calendar_events;
    ANALYZE chats;
    
    -- Analyze tasks table if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        ANALYZE tasks;
    END IF;
    
    RAISE NOTICE 'Table statistics updated';
END;
$$ LANGUAGE plpgsql;

-- Drop the helper function
DROP FUNCTION create_index_if_not_exists(text, text);