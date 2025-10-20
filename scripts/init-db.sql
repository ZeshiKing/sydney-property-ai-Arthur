-- Bootstrap schema for rental_aggregator database
-- This script is intentionally lightweight because SQLAlchemy
-- will create or migrate tables during application startup.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Placeholder table to verify connectivity during initialisation.
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
