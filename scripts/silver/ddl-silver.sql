
-- ==============================================================================
-- SILVER LAYER - Cleaned & Conformed Data
-- ==============================================================================

-- Table: silver.stores (SCD Type 2)
CREATE TABLE silver.stores (
    store_key SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    store_type VARCHAR(1) NOT NULL CHECK (store_type IN ('A', 'B', 'C')),
    store_size INTEGER NOT NULL CHECK (store_size > 0),
    effective_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_silver_stores_version UNIQUE (store_id, version),
    CONSTRAINT uq_silver_stores_effective UNIQUE (store_id, effective_date)
);

CREATE INDEX idx_silver_stores_id ON silver.stores (store_id);
CREATE INDEX idx_silver_stores_current ON silver.stores (store_id, is_current) WHERE is_current = TRUE;
CREATE INDEX idx_silver_stores_eff_date ON silver.stores (effective_date);

-- Table: silver.economic_features
CREATE TABLE silver.economic_features (
    feature_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    date DATE NOT NULL,
    temperature NUMERIC(5,2),
    fuel_price NUMERIC(5,3) CHECK (fuel_price >= 0),
    CASE WHEN markdown1 = 'NaN'::numeric OR markdown1 IS NULL THEN 0 ELSE markdown1 END,
    CASE WHEN markdown2 = 'NaN'::numeric OR markdown2 IS NULL THEN 0 ELSE markdown2 END,
    CASE WHEN markdown3 = 'NaN'::numeric OR markdown3 IS NULL THEN 0 ELSE markdown3 END,
    CASE WHEN markdown4 = 'NaN'::numeric OR markdown4 IS NULL THEN 0 ELSE markdown4 END,
    CASE WHEN markdown5 = 'NaN'::numeric OR markdown5 IS NULL THEN 0 ELSE markdown5 END,
    cpi NUMERIC(10,6) CHECK (cpi > 0),
    unemployment NUMERIC(5,3) CHECK (unemployment >= 0 AND unemployment <= 100),
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_silver_features UNIQUE (store_id, date)
);

CREATE INDEX idx_silver_features_date ON silver.economic_features (date);
CREATE INDEX idx_silver_features_store ON silver.economic_features (store_id);
CREATE INDEX idx_silver_features_store_date ON silver.economic_features (store_id, date);

-- Table: silver.sales
CREATE TABLE silver.sales (
    sales_id BIGSERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    date DATE NOT NULL,
    weekly_sales NUMERIC(12,2) NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_silver_sales UNIQUE (store_id, department_id, date)
);

CREATE INDEX idx_silver_sales_date ON silver.sales (date);
CREATE INDEX idx_silver_sales_store ON silver.sales (store_id);
CREATE INDEX idx_silver_sales_dept ON silver.sales (department_id);
CREATE INDEX idx_silver_sales_store_dept_date ON silver.sales (store_id, department_id, date);

