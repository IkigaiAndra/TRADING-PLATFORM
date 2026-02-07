-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create schema for trading analytics
CREATE SCHEMA IF NOT EXISTS trading;

-- Set search path
SET search_path TO trading, public;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialized successfully';
END $$;
