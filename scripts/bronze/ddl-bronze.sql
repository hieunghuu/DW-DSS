
-- ==============================================================================
-- BRONZE LAYER - Raw Data (Lossless Replication)
-- ==============================================================================

-- Table: bronze.stores
CREATE TABLE bronze.kaggle_stores (
    store INTEGER,
    type VARCHAR(1),
    size INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    source_file VARCHAR(255),
    row_hash VARCHAR(64)
) PARTITION BY RANGE (ingestion_timestamp);


-- Create partitions for bronze.stores
CREATE TABLE bronze.stores_2024 PARTITION OF bronze.kaggle_stores
     FOR VALUES FROM ('2026-1-1') TO ('2027-01-01');
 
CREATE INDEX idx_bronze_stores_ingest ON bronze.kaggle_stores (ingestion_timestamp);
CREATE INDEX idx_bronze_stores_hash ON bronze.kaggle_stores (row_hash);

-- Table: bronze.features
CREATE TABLE bronze.kaggle_features (
    store INTEGER,
    date DATE,
    temperature NUMERIC,
    fuel_price NUMERIC,
    markdown1 NUMERIC,
    markdown2 NUMERIC,
    markdown3 NUMERIC,
    markdown4 NUMERIC,
    markdown5 NUMERIC,
    cpi NUMERIC,
    unemployment NUMERIC,
    isholiday BOOLEAN,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    source_file VARCHAR(255),
    row_hash VARCHAR(64)
) PARTITION BY RANGE (ingestion_timestamp);

-- Create partitions for bronze.features
CREATE TABLE bronze.features_2026 PARTITION OF bronze.kaggle_features
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_bronze_features_ingest ON bronze.kaggle_features (ingestion_timestamp);
CREATE INDEX idx_bronze_features_date ON bronze.kaggle_features (date);
CREATE INDEX idx_bronze_features_hash ON bronze.kaggle_features (row_hash);

-- Table: bronze.sales
CREATE TABLE bronze.kaggle_sales (
    store INTEGER,
    dept INTEGER,
    date DATE,
    weekly_sales NUMERIC,
    isholiday BOOLEAN,
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),
    source_file VARCHAR(255),
    row_hash VARCHAR(64)
) PARTITION BY RANGE (ingestion_timestamp);

-- Create partitions for bronze.sales
CREATE TABLE bronze.sales_2026 PARTITION OF bronze.kaggle_sales
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_bronze_sales_ingest ON bronze.kaggle_sales (ingestion_timestamp);
CREATE INDEX idx_bronze_sales_date ON bronze.kaggle_sales (date);
CREATE INDEX idx_bronze_sales_store_dept ON bronze.kaggle_sales (store, dept);
CREATE INDEX idx_bronze_sales_hash ON bronze.kaggle_sales (row_hash);
