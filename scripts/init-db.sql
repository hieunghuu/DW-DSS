-- ==============================================================================
-- WALMART DSS - COMPLETE DATABASE SCHEMA
-- 4-Layer Medallion Architecture: Bronze → Silver → Platinum → Gold
-- Database: PostgreSQL 15+
-- Author: Data Engineering Team
-- Date: 2024-02-08
-- ==============================================================================

-- Create database and schemas
CREATE DATABASE walmart_dwh;

CREATE SCHEMA bronze;
CREATE SCHEMA silver;
CREATE SCHEMA platinum;
CREATE SCHEMA gold;

-- Set search path
SET search_path TO bronze, silver, platinum, gold, public;