
-- ==============================================================================
-- GOLD LAYER - Star Schema (Enterprise DWH)
-- ==============================================================================

-- DIMENSION: gold.dim_date
CREATE TABLE gold.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    year_quarter VARCHAR(7),
    year_month VARCHAR(7),
    year_week VARCHAR(8),
    month_number INTEGER NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    month_name VARCHAR(10) NOT NULL,
    month_abbr VARCHAR(3) NOT NULL,
    quarter_number INTEGER NOT NULL CHECK (quarter_number BETWEEN 1 AND 4),
    quarter_name VARCHAR(2),
    week_of_year INTEGER NOT NULL CHECK (week_of_year BETWEEN 1 AND 53),
    week_of_month INTEGER,
    day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    day_of_year INTEGER NOT NULL CHECK (day_of_year BETWEEN 1 AND 366),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_name VARCHAR(10) NOT NULL,
    day_abbr VARCHAR(3) NOT NULL,
    is_weekend BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(50),
    is_business_day BOOLEAN DEFAULT TRUE,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER,
    fiscal_period INTEGER,
    event_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dim_date_full_date ON gold.dim_date (full_date);
CREATE INDEX idx_dim_date_year_month ON gold.dim_date (year, month_number);
CREATE INDEX idx_dim_date_quarter ON gold.dim_date (year, quarter_number);
CREATE INDEX idx_dim_date_holiday ON gold.dim_date (is_holiday) WHERE is_holiday = TRUE;

-- Populate dim_date with 10 years of dates
INSERT INTO gold.dim_date (
    date_key, full_date, year, month_number, quarter_number, 
    week_of_year, day_of_month, day_of_year, day_of_week,
    day_name, day_abbr, month_name, month_abbr, quarter_name,
    year_quarter, year_month, year_week, is_weekend
)
SELECT 
    TO_CHAR(date_series, 'YYYYMMDD')::INTEGER AS date_key,
    date_series AS full_date,
    EXTRACT(YEAR FROM date_series)::INTEGER AS year,
    EXTRACT(MONTH FROM date_series)::INTEGER AS month_number,
    EXTRACT(QUARTER FROM date_series)::INTEGER AS quarter_number,
    EXTRACT(WEEK FROM date_series)::INTEGER AS week_of_year,
    EXTRACT(DAY FROM date_series)::INTEGER AS day_of_month,
    EXTRACT(DOY FROM date_series)::INTEGER AS day_of_year,
    EXTRACT(ISODOW FROM date_series)::INTEGER AS day_of_week,
    TO_CHAR(date_series, 'Day') AS day_name,
    TO_CHAR(date_series, 'Dy') AS day_abbr,
    TO_CHAR(date_series, 'Month') AS month_name,
    TO_CHAR(date_series, 'Mon') AS month_abbr,
    'Q' || EXTRACT(QUARTER FROM date_series) AS quarter_name,
    EXTRACT(YEAR FROM date_series) || '-Q' || EXTRACT(QUARTER FROM date_series) AS year_quarter,
    TO_CHAR(date_series, 'YYYY-MM') AS year_month,
    EXTRACT(YEAR FROM date_series) || '-W' || LPAD(EXTRACT(WEEK FROM date_series)::TEXT, 2, '0') AS year_week,
    CASE WHEN EXTRACT(ISODOW FROM date_series) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2010-01-01'::date, '2020-12-31'::date, '1 day'::interval) AS date_series;

-- DIMENSION: gold.dim_store (Type 2 SCD)
CREATE TABLE gold.dim_store (
    store_key SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL,
    store_type VARCHAR(1) NOT NULL CHECK (store_type IN ('A', 'B', 'C')),
    store_type_description VARCHAR(50),
    store_size INTEGER NOT NULL CHECK (store_size > 0),
    size_category VARCHAR(20),
    region VARCHAR(50),
    state VARCHAR(50),
    city VARCHAR(100),
    sales_per_sqft_avg DECIMAL(10,2),
    store_efficiency_rank INTEGER,
    effective_date DATE NOT NULL,
    end_date DATE DEFAULT '9999-12-31',
    is_current BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_dim_store_version UNIQUE (store_id, version)
);

CREATE INDEX idx_dim_store_id ON gold.dim_store (store_id);
CREATE INDEX idx_dim_store_current ON gold.dim_store (store_id, is_current) WHERE is_current = TRUE;
CREATE INDEX idx_dim_store_type ON gold.dim_store (store_type);
CREATE INDEX idx_dim_store_eff_date ON gold.dim_store (effective_date);

-- DIMENSION: gold.dim_department
CREATE TABLE gold.dim_department (
    department_key SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL UNIQUE,
    department_name VARCHAR(100),
    department_category VARCHAR(50),
    department_group VARCHAR(50),
    division VARCHAR(50),
    is_seasonal BOOLEAN DEFAULT FALSE,
    is_high_margin BOOLEAN DEFAULT FALSE,
    avg_margin_pct DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dim_dept_category ON gold.dim_department (department_category);

-- Populate dim_department with default values (1-99)
INSERT INTO gold.dim_department (department_id, department_name, department_category, department_group)
SELECT 
    dept_id,
    'Department ' || dept_id AS department_name,
    CASE 
        WHEN dept_id <= 30 THEN 'General Merchandise'
        WHEN dept_id <= 60 THEN 'Food'
        WHEN dept_id <= 90 THEN 'Apparel'
        ELSE 'Other'
    END AS department_category,
    CASE 
        WHEN dept_id <= 45 THEN 'Discretionary'
        ELSE 'Staples'
    END AS department_group
FROM generate_series(1, 99) AS dept_id;

-- DIMENSION: gold.dim_promotion (Junk Dimension)
CREATE TABLE gold.dim_promotion (
    promotion_key SERIAL PRIMARY KEY,
    markdown1 DECIMAL(12,2) DEFAULT 0,
    markdown2 DECIMAL(12,2) DEFAULT 0,
    markdown3 DECIMAL(12,2) DEFAULT 0,
    markdown4 DECIMAL(12,2) DEFAULT 0,
    markdown5 DECIMAL(12,2) DEFAULT 0,
    total_markdown DECIMAL(12,2) GENERATED ALWAYS AS 
        (markdown1 + markdown2 + markdown3 + markdown4 + markdown5) STORED,
    has_markdown1 BOOLEAN GENERATED ALWAYS AS (markdown1 > 0) STORED,
    has_markdown2 BOOLEAN GENERATED ALWAYS AS (markdown2 > 0) STORED,
    has_markdown3 BOOLEAN GENERATED ALWAYS AS (markdown3 > 0) STORED,
    has_markdown4 BOOLEAN GENERATED ALWAYS AS (markdown4 > 0) STORED,
    has_markdown5 BOOLEAN GENERATED ALWAYS AS (markdown5 > 0) STORED,
    num_markdowns INTEGER GENERATED ALWAYS AS 
        ((markdown1 > 0)::int + (markdown2 > 0)::int + (markdown3 > 0)::int + 
         (markdown4 > 0)::int + (markdown5 > 0)::int) STORED,
    promotion_type VARCHAR(50),
    promotion_intensity VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_dim_promotion UNIQUE (markdown1, markdown2, markdown3, markdown4, markdown5)
);

CREATE INDEX idx_dim_promo_type ON gold.dim_promotion (promotion_type);
CREATE INDEX idx_dim_promo_intensity ON gold.dim_promotion (promotion_intensity);

-- Insert default "No Promotion" row
INSERT INTO gold.dim_promotion (promotion_key, markdown1, markdown2, markdown3, markdown4, markdown5, promotion_type)
VALUES (0, 0, 0, 0, 0, 0, 'None')
ON CONFLICT DO NOTHING;

-- DIMENSION: gold.dim_economic_factors (Mini-Dimension)
CREATE TABLE gold.dim_economic_factors (
    economic_key SERIAL PRIMARY KEY,
    temperature DECIMAL(5,2),
    temperature_band VARCHAR(20),
    fuel_price DECIMAL(5,3),
    fuel_price_band VARCHAR(20),
    cpi DECIMAL(10,6),
    cpi_category VARCHAR(20),
    unemployment DECIMAL(5,3),
    unemployment_category VARCHAR(20),
    economic_condition VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_dim_economic UNIQUE (temperature, fuel_price, cpi, unemployment)
);

CREATE INDEX idx_dim_econ_condition ON gold.dim_economic_factors (economic_condition);

-- Insert default "Unknown" row
INSERT INTO gold.dim_economic_factors (economic_key, economic_condition)
VALUES (0, 'Unknown')
ON CONFLICT DO NOTHING;

-- FACT TABLE: gold.fact_sales
CREATE TABLE gold.fact_sales (
    sales_key BIGSERIAL PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES gold.dim_date(date_key),
    store_key INTEGER NOT NULL REFERENCES gold.dim_store(store_key),
    department_key INTEGER NOT NULL REFERENCES gold.dim_department(department_key),
    promotion_key INTEGER NOT NULL REFERENCES gold.dim_promotion(promotion_key),
    economic_key INTEGER NOT NULL REFERENCES gold.dim_economic_factors(economic_key),
    is_holiday BOOLEAN DEFAULT FALSE,
    weekly_sales DECIMAL(12,2) NOT NULL,
    sales_quantity INTEGER DEFAULT 0,
    sales_vs_ly DECIMAL(12,2),
    sales_growth_pct DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_fact_sales UNIQUE (date_key, store_key, department_key)
);

CREATE INDEX idx_fact_date ON gold.fact_sales (date_key);
CREATE INDEX idx_fact_store ON gold.fact_sales (store_key);
CREATE INDEX idx_fact_dept ON gold.fact_sales (department_key);
CREATE INDEX idx_fact_promo ON gold.fact_sales (promotion_key);
CREATE INDEX idx_fact_econ ON gold.fact_sales (economic_key);
CREATE INDEX idx_fact_composite ON gold.fact_sales (date_key, store_key, department_key);
CREATE INDEX idx_fact_sales_amount ON gold.fact_sales (weekly_sales);

-- ==============================================================================
-- ROLES & PERMISSIONS
-- ==============================================================================

-- Create roles
-- CREATE ROLE dw_admin;
-- CREATE ROLE dw_analyst;
-- CREATE ROLE dw_developer;

-- Grant privileges
-- Admin: full access
GRANT ALL PRIVILEGES ON SCHEMA bronze, silver, platinum, gold TO dw_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bronze, silver, platinum, gold TO dw_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bronze, silver, platinum, gold TO dw_admin;

-- Analyst: read-only on Gold
GRANT USAGE ON SCHEMA gold TO dw_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO dw_analyst;

-- Developer: read/write on Bronze, Silver, Platinum
GRANT USAGE ON SCHEMA bronze, silver, platinum TO dw_developer;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA bronze, silver, platinum TO dw_developer;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA bronze, silver, platinum TO dw_developer;

-- ==============================================================================
-- VIEWS & HELPER FUNCTIONS
-- ==============================================================================

-- View: Current stores (latest version only)
CREATE OR REPLACE VIEW gold.v_current_stores AS
SELECT 
    store_key,
    store_id,
    store_type,
    store_type_description,
    store_size,
    size_category,
    region,
    state,
    city
FROM gold.dim_store
WHERE is_current = TRUE;

-- View: Sales summary by store type
CREATE OR REPLACE VIEW gold.v_sales_by_store_type AS
SELECT 
    ds.store_type,
    dd.year,
    dd.quarter_name,
    COUNT(DISTINCT ds.store_id) AS num_stores,
    SUM(fs.weekly_sales) AS total_sales,
    AVG(fs.weekly_sales) AS avg_weekly_sales,
    MAX(fs.weekly_sales) AS max_weekly_sales,
    MIN(fs.weekly_sales) AS min_weekly_sales
FROM gold.fact_sales fs
JOIN gold.dim_store ds ON fs.store_key = ds.store_key
JOIN gold.dim_date dd ON fs.date_key = dd.date_key
GROUP BY ds.store_type, dd.year, dd.quarter_name;

-- View: Promotion effectiveness summary
CREATE OR REPLACE VIEW gold.v_promotion_effectiveness AS
SELECT 
    dp.promotion_type,
    dp.num_markdowns,
    COUNT(*) AS num_observations,
    SUM(fs.weekly_sales) AS total_sales,
    AVG(fs.weekly_sales) AS avg_sales,
    AVG(dp.total_markdown) AS avg_markdown_cost,
    SUM(fs.weekly_sales) / NULLIF(SUM(dp.total_markdown), 0) AS roi
FROM gold.fact_sales fs
JOIN gold.dim_promotion dp ON fs.promotion_key = dp.promotion_key
WHERE dp.promotion_type != 'None'
GROUP BY dp.promotion_type, dp.num_markdowns;

-- ==============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ==============================================================================

COMMENT ON SCHEMA bronze IS '4-Layer Medallion: Bronze layer - Raw data from source systems';
COMMENT ON SCHEMA silver IS '4-Layer Medallion: Silver layer - Cleaned and conformed data';
COMMENT ON SCHEMA platinum IS '4-Layer Medallion: Platinum layer - Business domain marts';
COMMENT ON SCHEMA gold IS '4-Layer Medallion: Gold layer - Star schema for enterprise reporting';

COMMENT ON TABLE gold.fact_sales IS 'Central fact table: Weekly sales by store and department';
COMMENT ON TABLE gold.dim_date IS 'Date dimension with time hierarchies';
COMMENT ON TABLE gold.dim_store IS 'Store dimension with Type 2 SCD for historical tracking';
COMMENT ON TABLE gold.dim_department IS 'Department dimension';
COMMENT ON TABLE gold.dim_promotion IS 'Junk dimension for promotion combinations';
COMMENT ON TABLE gold.dim_economic_factors IS 'Mini-dimension for economic indicators';