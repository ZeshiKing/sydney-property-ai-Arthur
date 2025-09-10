-- Initialize database for rental aggregator
-- This script runs automatically when PostgreSQL container starts

-- Create database if it doesn't exist (redundant since specified in docker-compose)
-- CREATE DATABASE IF NOT EXISTS rental_aggregator;

-- Connect to the database
\c rental_aggregator;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create search_history table
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    search_id VARCHAR(255) UNIQUE NOT NULL,
    search_params JSONB NOT NULL,
    result_count INTEGER NOT NULL,
    execution_time INTEGER NOT NULL,
    sources_scrapped JSONB NOT NULL,
    user_ip INET,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create properties table
CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    property_id VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    address_data JSONB NOT NULL,
    price_data JSONB NOT NULL,
    property_details JSONB NOT NULL,
    media_data JSONB NOT NULL,
    description TEXT,
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    contact_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    availability_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(property_id, source)
);

-- Create scraping_jobs table
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    job_params JSONB NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    user_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result_data JSONB,
    execution_time INTEGER,
    errors JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at);
CREATE INDEX IF NOT EXISTS idx_search_history_search_params ON search_history USING GIN (search_params);

CREATE INDEX IF NOT EXISTS idx_properties_location ON properties USING GIN ((address_data->>'suburb'), (address_data->>'state'));
CREATE INDEX IF NOT EXISTS idx_properties_price ON properties USING BTREE (((price_data->>'amount')::numeric));
CREATE INDEX IF NOT EXISTS idx_properties_bedrooms ON properties USING BTREE (((property_details->>'bedrooms')::integer));
CREATE INDEX IF NOT EXISTS idx_properties_source_updated ON properties(source, updated_at);
CREATE INDEX IF NOT EXISTS idx_properties_property_type ON properties USING BTREE ((property_details->>'type'));

CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_type ON scraping_jobs(job_type, created_at);

-- Create updated_at trigger for properties table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_properties_updated_at 
    BEFORE UPDATE ON properties 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create some sample data for testing (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM search_history LIMIT 1) THEN
        INSERT INTO search_history (search_id, search_params, result_count, execution_time, sources_scrapped)
        VALUES (
            'sample_search_001',
            '{"listingType": "rent", "location": {"suburb": "Camperdown", "state": "NSW", "postcode": "2050"}}',
            5,
            1250,
            '["database"]'
        );
    END IF;
END $$;

-- Grant permissions (if needed for specific user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rental_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rental_user;

-- Display table information
\dt

-- Display table sizes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

ANALYZE;

-- Show completion message
SELECT 'Database initialization completed successfully!' as message;