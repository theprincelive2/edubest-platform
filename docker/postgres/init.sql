-- ============================================================
-- PostgreSQL Initialization Script for Edubest
-- This runs once when the container is first created
-- ============================================================

-- Enable UUID extension (used for primary keys in some models)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for full-text search on names
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable citext for case-insensitive text (emails)
CREATE EXTENSION IF NOT EXISTS citext;

-- Create the public schema (shared tables for django-tenants)
-- This already exists by default, but we ensure it's set up correctly.

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON DATABASE edubest TO edubest_user;
GRANT ALL ON SCHEMA public TO edubest_user;

-- Set timezone to UTC (important for multi-school global deployment)
ALTER DATABASE edubest SET timezone TO 'UTC';
