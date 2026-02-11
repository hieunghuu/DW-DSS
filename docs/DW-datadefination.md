# DATA DEFINITION DOCUMENT
## Walmart DSS - 4-Layer Medallion Architecture

**Document Version:** 1.0  
**Date:** 2024-02-08  
**Author:** Data Engineering Team  
**Database:** PostgreSQL 15+  

---

## TABLE OF CONTENTS

1. [BRONZE LAYER](#bronze-layer)
   - bronze.stores
   - bronze.features
   - bronze.sales

2. [SILVER LAYER](#silver-layer)
   - silver.stores
   - silver.economic_features
   - silver.sales

3. [PLATINUM LAYER](#platinum-layer)
   - platinum.promotion_effectiveness
   - platinum.sales_trend_analysis

4. [GOLD LAYER](#gold-layer)
   - gold.dim_date
   - gold.dim_store
   - gold.dim_department
   - gold.dim_promotion
   - gold.dim_economic_factors
   - gold.fact_sales

---

# BRONZE LAYER

## bronze.stores

### Description
Thông tin cửa hàng Walmart. Dữ liệu thô từ file stores.csv, không thay đổi.

### Grain
One row per store

### Source
stores.csv (45 rows)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | Description |
|---|-------------|-----------|----------|---------|-------------|
| 1 | store | INTEGER | NOT NULL | - | Store identifier. Range: 1-45. Business key. |
| 2 | type | VARCHAR(1) | NOT NULL | - | Store type classification. Values: 'A' (Superstore), 'B' (Discount), 'C' (Neighborhood). |
| 3 | size | INTEGER | NOT NULL | - | Store size in square feet. Range: 34,875 - 219,622. |
| 4 | ingestion_timestamp | TIMESTAMP | NOT NULL | NOW() | Timestamp when record was loaded into database. |
| 5 | source_file | VARCHAR(255) | NULL | - | Source CSV filename. Example: 'stores.csv'. |
| 6 | row_hash | VARCHAR(64) | NULL | - | MD5 hash of row content for deduplication. |

### Constraints
- **Primary Key:** None (raw data)
- **Unique Constraints:** None
- **Check Constraints:** None
- **Foreign Keys:** None

### Indexes
```sql
CREATE INDEX idx_bronze_stores_store ON bronze.stores (store);
CREATE INDEX idx_bronze_stores_ingest ON bronze.stores (ingestion_timestamp);
```

### Business Rules
1. Store ID must be unique in source file
2. Store type must be A, B, or C
3. Store size must be positive integer
4. Data is immutable (append-only)

### Data Quality
- **Completeness:** 100% (all stores have all fields)
- **Validity:** Store types validated at Silver layer
- **Duplicates:** Handled via row_hash

---

## bronze.features

### Description
Dữ liệu kinh tế và khuyến mãi theo tuần. Bao gồm temperature, fuel price, markdowns, CPI, unemployment.

### Grain
One row per store per week

### Source
features.csv (8,190 rows)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | Description |
|---|-------------|-----------|----------|---------|-------------|
| 1 | store | INTEGER | NOT NULL | - | Store identifier. Foreign key to stores. Range: 1-45. |
| 2 | date | DATE | NOT NULL | - | Week ending date (always Friday). Range: 2010-02-05 to 2012-10-26. |
| 3 | temperature | NUMERIC | NULL | - | Average temperature in Fahrenheit. Range: 5.54 to 100.14. |
| 4 | fuel_price | NUMERIC | NULL | - | Regional fuel price in USD per gallon. Range: 2.472 to 4.468. |
| 5 | markdown1 | NUMERIC | NULL | - | Promotional markdown amount type 1 in USD. Can be NaN. Range: 0 to ~20,000. |
| 6 | markdown2 | NUMERIC | NULL | - | Promotional markdown amount type 2 in USD. Can be NaN. Range: 0 to ~10,000. |
| 7 | markdown3 | NUMERIC | NULL | - | Promotional markdown amount type 3 in USD. Can be NaN. Range: 0 to ~5,000. |
| 8 | markdown4 | NUMERIC | NULL | - | Promotional markdown amount type 4 in USD. Can be NaN. Range: 0 to ~3,000. |
| 9 | markdown5 | NUMERIC | NULL | - | Promotional markdown amount type 5 in USD. Can be NaN. Range: 0 to ~1,000. |
| 10 | cpi | NUMERIC | NULL | - | Consumer Price Index. Range: 126.064 to 228.976. |
| 11 | unemployment | NUMERIC | NULL | - | Unemployment rate in percentage. Range: 3.879 to 14.313. |
| 12 | isholiday | BOOLEAN | NOT NULL | - | Flag indicating if the week contains a major holiday. Values: TRUE, FALSE. |
| 13 | ingestion_timestamp | TIMESTAMP | NOT NULL | NOW() | Timestamp when record was loaded. |
| 14 | source_file | VARCHAR(255) | NULL | - | Source CSV filename. Example: 'features.csv'. |
| 15 | row_hash | VARCHAR(64) | NULL | - | MD5 hash for deduplication. |

### Constraints
- **Primary Key:** None (raw data)
- **Unique Constraints:** None
- **Check Constraints:** None
- **Foreign Keys:** None

### Indexes
```sql
CREATE INDEX idx_bronze_features_store ON bronze.features (store);
CREATE INDEX idx_bronze_features_date ON bronze.features (date);
CREATE INDEX idx_bronze_features_store_date ON bronze.features (store, date);
```

### Business Rules
1. (Store, Date) combination should be unique
2. Date must be Friday (week ending)
3. Markdown values NaN represent "no promotion"
4. Holiday flag should align with known US retail holidays
5. CPI and unemployment must be positive

### Data Quality
- **Completeness:** 
  - Temperature: ~85% populated
  - Fuel_price: ~95% populated
  - Markdowns: ~30-40% NaN (normal - no promotion)
  - CPI, Unemployment: 100% populated
- **Validity:** Validated at Silver layer
- **NaN Handling:** Converted to 0 in Silver layer

---

## bronze.sales

### Description
Weekly sales data by store and department. Primary transaction data for analysis.

### Grain
One row per store per department per week

### Source
train.csv (421,570 rows)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | Description |
|---|-------------|-----------|----------|---------|-------------|
| 1 | store | INTEGER | NOT NULL | - | Store identifier. Range: 1-45. |
| 2 | dept | INTEGER | NOT NULL | - | Department identifier. Range: 1-99. |
| 3 | date | DATE | NOT NULL | - | Week ending date (Friday). Range: 2010-02-05 to 2012-10-26. |
| 4 | weekly_sales | NUMERIC | NOT NULL | - | Weekly sales amount in USD. Can be negative (returns > sales). Range: -4,988.94 to 693,099.36. |
| 5 | isholiday | BOOLEAN | NOT NULL | - | Holiday week flag. Values: TRUE, FALSE. |
| 6 | ingestion_timestamp | TIMESTAMP | NOT NULL | NOW() | Record load timestamp. |
| 7 | source_file | VARCHAR(255) | NULL | - | Source filename. Example: 'train.csv'. |
| 8 | row_hash | VARCHAR(64) | NULL | - | MD5 hash for deduplication. |

### Constraints
- **Primary Key:** None (raw data)
- **Unique Constraints:** None
- **Check Constraints:** None
- **Foreign Keys:** None

### Indexes
```sql
CREATE INDEX idx_bronze_sales_store ON bronze.sales (store);
CREATE INDEX idx_bronze_sales_dept ON bronze.sales (dept);
CREATE INDEX idx_bronze_sales_date ON bronze.sales (date);
CREATE INDEX idx_bronze_sales_store_dept_date ON bronze.sales (store, dept, date);
```

### Business Rules
1. (Store, Dept, Date) combination should be unique
2. Weekly_sales can be negative (valid returns case)
3. Date should match with features.date
4. Not all department/store combinations exist
5. Holiday flag should match features.isholiday

### Data Quality
- **Completeness:** 100% (all required fields populated)
- **Negative Sales:** ~1% of records (valid business case)
- **Missing Combinations:** Normal - not all depts in all stores
- **Date Alignment:** Should match features table dates

---

# SILVER LAYER

## silver.stores

### Description
Cleaned store dimension with Type 2 Slowly Changing Dimension tracking. Tracks historical changes to store attributes.

### Grain
One row per store per version

### Source
bronze.stores

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | store_key | SERIAL | NOT NULL | AUTO | PK | Surrogate key. Unique identifier for each store version. |
| 2 | store_id | INTEGER | NOT NULL | - | NK | Natural key. Business identifier (1-45). |
| 3 | store_type | VARCHAR(1) | NOT NULL | - | - | Store classification. Values: 'A', 'B', 'C'. |
| 4 | store_size | INTEGER | NOT NULL | - | - | Size in square feet. Must be > 0. |
| 5 | effective_date | DATE | NOT NULL | '2010-02-05' | - | Date when this version became effective. |
| 6 | end_date | DATE | NOT NULL | '9999-12-31' | - | Date when this version expired. '9999-12-31' for current. |
| 7 | is_current | BOOLEAN | NOT NULL | TRUE | - | Flag indicating if this is the current version. |
| 8 | version | INTEGER | NOT NULL | 1 | - | Version number starting from 1. |
| 9 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |
| 10 | updated_at | TIMESTAMP | NOT NULL | NOW() | - | Last update timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE silver.stores ADD PRIMARY KEY (store_key);

-- Unique Constraints
ALTER TABLE silver.stores ADD CONSTRAINT uq_silver_stores_version 
    UNIQUE (store_id, version);
ALTER TABLE silver.stores ADD CONSTRAINT uq_silver_stores_effective 
    UNIQUE (store_id, effective_date);

-- Check Constraints
ALTER TABLE silver.stores ADD CONSTRAINT chk_store_type 
    CHECK (store_type IN ('A', 'B', 'C'));
ALTER TABLE silver.stores ADD CONSTRAINT chk_store_size 
    CHECK (store_size > 0);
ALTER TABLE silver.stores ADD CONSTRAINT chk_dates 
    CHECK (effective_date <= end_date);
```

### Indexes
```sql
CREATE INDEX idx_silver_stores_id ON silver.stores (store_id);
CREATE INDEX idx_silver_stores_current ON silver.stores (store_id, is_current) 
    WHERE is_current = TRUE;
CREATE INDEX idx_silver_stores_eff_date ON silver.stores (effective_date);
```

### Business Rules
1. One and only one current version per store (is_current = TRUE)
2. Versions ordered by effective_date
3. No gaps in date ranges for same store_id
4. end_date = '9999-12-31' indicates current record
5. New version created when store_type or store_size changes
6. effective_date of new version = end_date of previous version + 1 day

### SCD Type 2 Logic
```sql
-- When store changes:
-- 1. Close previous record (set end_date, is_current = FALSE)
UPDATE silver.stores 
SET end_date = '2011-06-30', is_current = FALSE
WHERE store_id = 1 AND is_current = TRUE;

-- 2. Insert new version
INSERT INTO silver.stores (store_id, store_type, store_size, effective_date, version)
VALUES (1, 'A', 180000, '2011-07-01', 2);
```

---

## silver.economic_features

### Description
Cleaned economic indicators and promotional markdowns. NaN values converted to 0, data validated.

### Grain
One row per store per week

### Source
bronze.features

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | feature_id | SERIAL | NOT NULL | AUTO | PK | Surrogate key. |
| 2 | store_id | INTEGER | NOT NULL | - | NK | Store identifier (1-45). |
| 3 | date | DATE | NOT NULL | - | NK | Week ending date. |
| 4 | temperature | NUMERIC(5,2) | NULL | - | - | Average temperature in °F. Precision: XX.XX |
| 5 | fuel_price | NUMERIC(5,3) | NULL | - | - | Fuel price $/gallon. Precision: X.XXX. Must be >= 0. |
| 6 | markdown1 | NUMERIC(12,2) | NOT NULL | 0 | - | Markdown type 1 ($). NaN converted to 0. Precision: XXXXXXXXXX.XX |
| 7 | markdown2 | NUMERIC(12,2) | NOT NULL | 0 | - | Markdown type 2 ($). NaN converted to 0. |
| 8 | markdown3 | NUMERIC(12,2) | NOT NULL | 0 | - | Markdown type 3 ($). NaN converted to 0. |
| 9 | markdown4 | NUMERIC(12,2) | NOT NULL | 0 | - | Markdown type 4 ($). NaN converted to 0. |
| 10 | markdown5 | NUMERIC(12,2) | NOT NULL | 0 | - | Markdown type 5 ($). NaN converted to 0. |
| 11 | cpi | NUMERIC(10,6) | NULL | - | - | Consumer Price Index. Precision: XXXX.XXXXXX. Must be > 0. |
| 12 | unemployment | NUMERIC(5,3) | NULL | - | - | Unemployment rate %. Precision: XX.XXX. Range: 0-100. |
| 13 | is_holiday | BOOLEAN | NOT NULL | FALSE | - | Holiday week flag. |
| 14 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE silver.economic_features ADD PRIMARY KEY (feature_id);

-- Unique Constraint
ALTER TABLE silver.economic_features ADD CONSTRAINT uq_silver_features 
    UNIQUE (store_id, date);

-- Check Constraints
ALTER TABLE silver.economic_features ADD CONSTRAINT chk_fuel_price 
    CHECK (fuel_price >= 0 OR fuel_price IS NULL);
ALTER TABLE silver.economic_features ADD CONSTRAINT chk_cpi 
    CHECK (cpi > 0 OR cpi IS NULL);
ALTER TABLE silver.economic_features ADD CONSTRAINT chk_unemployment 
    CHECK (unemployment >= 0 AND unemployment <= 100 OR unemployment IS NULL);
```

### Indexes
```sql
CREATE INDEX idx_silver_features_date ON silver.economic_features (date);
CREATE INDEX idx_silver_features_store ON silver.economic_features (store_id);
CREATE INDEX idx_silver_features_store_date ON silver.economic_features (store_id, date);
```

### Business Rules
1. (Store_id, Date) must be unique
2. All markdown NaN values converted to 0.00
3. Markdown values cannot be negative
4. CPI must be positive (economic indicator validation)
5. Unemployment must be 0-100%
6. Date must be Friday (week ending)

### Transformation Logic
```sql
-- NaN to 0 conversion
COALESCE(NULLIF(markdown1, 'NaN'::numeric), 0)

-- Type precision
temperature::NUMERIC(5,2)   -- 72.31
fuel_price::NUMERIC(5,3)    -- 2.572
markdown1::NUMERIC(12,2)    -- 1234.56
cpi::NUMERIC(10,6)          -- 211.096500
unemployment::NUMERIC(5,3)  -- 8.106
```

---

## silver.sales

### Description
Cleaned weekly sales data. Deduplicated, type-casted, NULL sales removed.

### Grain
One row per store per department per week

### Source
bronze.sales

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | sales_id | BIGSERIAL | NOT NULL | AUTO | PK | Surrogate key. |
| 2 | store_id | INTEGER | NOT NULL | - | NK | Store identifier (1-45). |
| 3 | department_id | INTEGER | NOT NULL | - | NK | Department identifier (1-99). |
| 4 | date | DATE | NOT NULL | - | NK | Week ending date. |
| 5 | weekly_sales | NUMERIC(12,2) | NOT NULL | - | - | Weekly sales amount ($). Can be negative. Precision: XXXXXXXXXX.XX |
| 6 | is_holiday | BOOLEAN | NOT NULL | FALSE | - | Holiday week flag. |
| 7 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE silver.sales ADD PRIMARY KEY (sales_id);

-- Unique Constraint
ALTER TABLE silver.sales ADD CONSTRAINT uq_silver_sales 
    UNIQUE (store_id, department_id, date);

-- Check Constraints (none - negative sales allowed)
```

### Indexes
```sql
CREATE INDEX idx_silver_sales_date ON silver.sales (date);
CREATE INDEX idx_silver_sales_store ON silver.sales (store_id);
CREATE INDEX idx_silver_sales_dept ON silver.sales (department_id);
CREATE INDEX idx_silver_sales_store_dept_date ON silver.sales (store_id, department_id, date);
```

### Business Rules
1. (Store_id, Department_id, Date) must be unique
2. Weekly_sales cannot be NULL
3. Weekly_sales can be negative (returns exceed sales)
4. Date must match with economic_features dates
5. Store_id must exist in stores table
6. Date must be Friday (week ending)

### Transformation Logic
```sql
-- Deduplication on conflict
INSERT INTO silver.sales (store_id, department_id, date, weekly_sales, is_holiday)
SELECT store, dept, date::DATE, weekly_sales::NUMERIC(12,2), isholiday
FROM bronze.sales
WHERE weekly_sales IS NOT NULL
ON CONFLICT (store_id, department_id, date) 
DO UPDATE SET weekly_sales = EXCLUDED.weekly_sales;
```

---

# PLATINUM LAYER

## platinum.promotion_effectiveness

### Description
Materialized view analyzing promotional effectiveness. Pre-aggregated KPIs for marketing analytics.

### Grain
One row per store per department per week

### Source
silver.sales, silver.economic_features, silver.stores

### View Structure

| # | Column Name | Data Type | Nullable | Description |
|---|-------------|-----------|----------|-------------|
| 1 | store_id | INTEGER | NOT NULL | Store identifier. |
| 2 | store_type | VARCHAR(1) | NULL | Store classification (A/B/C). |
| 3 | store_size | INTEGER | NULL | Store size in sq ft. |
| 4 | week_start | DATE | NOT NULL | Week starting date (Monday). |
| 5 | department_id | INTEGER | NOT NULL | Department identifier. |
| 6 | total_sales | NUMERIC(14,2) | NULL | Sum of weekly sales for the period. |
| 7 | avg_sales | NUMERIC(12,2) | NULL | Average weekly sales. |
| 8 | avg_markdown1 | NUMERIC(12,2) | NULL | Average markdown1 amount. |
| 9 | avg_markdown2 | NUMERIC(12,2) | NULL | Average markdown2 amount. |
| 10 | avg_markdown3 | NUMERIC(12,2) | NULL | Average markdown3 amount. |
| 11 | avg_markdown4 | NUMERIC(12,2) | NULL | Average markdown4 amount. |
| 12 | avg_markdown5 | NUMERIC(12,2) | NULL | Average markdown5 amount. |
| 13 | has_markdown1 | BOOLEAN | NULL | Flag if any markdown1 > 0. |
| 14 | has_markdown2 | BOOLEAN | NULL | Flag if any markdown2 > 0. |
| 15 | has_markdown3 | BOOLEAN | NULL | Flag if any markdown3 > 0. |
| 16 | has_markdown4 | BOOLEAN | NULL | Flag if any markdown4 > 0. |
| 17 | has_markdown5 | BOOLEAN | NULL | Flag if any markdown5 > 0. |
| 18 | promotion_roi | NUMERIC(12,2) | NULL | Calculated: total_sales / total_markdown. |
| 19 | has_holiday | BOOLEAN | NULL | Holiday week flag. |

### Indexes
```sql
CREATE UNIQUE INDEX idx_plat_promo_unique 
    ON platinum.promotion_effectiveness (store_id, department_id, week_start);
CREATE INDEX idx_plat_promo_week 
    ON platinum.promotion_effectiveness (week_start);
CREATE INDEX idx_plat_promo_store 
    ON platinum.promotion_effectiveness (store_id);
```

### Calculated Fields

**promotion_roi:**
```sql
total_sales / NULLIF(
    COALESCE(SUM(markdown1), 0) + 
    COALESCE(SUM(markdown2), 0) + 
    COALESCE(SUM(markdown3), 0) + 
    COALESCE(SUM(markdown4), 0) + 
    COALESCE(SUM(markdown5), 0), 
    0
)
```

### Business Rules
1. ROI calculation handles divide-by-zero (returns NULL)
2. Week_start calculated as Monday of the week
3. Only current store versions included
4. All markdowns averaged over the aggregation period

### Refresh Schedule
Daily at 3 AM via `REFRESH MATERIALIZED VIEW CONCURRENTLY`

---

## platinum.sales_trend_analysis

### Description
Materialized view for time-series analysis. Includes YoY comparisons and economic indicators.

### Grain
One row per store per department per week

### Source
silver.sales, silver.stores, silver.economic_features

### View Structure

| # | Column Name | Data Type | Nullable | Description |
|---|-------------|-----------|----------|-------------|
| 1 | store_id | INTEGER | NOT NULL | Store identifier. |
| 2 | store_type | VARCHAR(1) | NULL | Store classification. |
| 3 | department_id | INTEGER | NOT NULL | Department identifier. |
| 4 | week_start | DATE | NOT NULL | Week starting date (Monday). |
| 5 | month_start | DATE | NOT NULL | Month starting date. |
| 6 | quarter_start | DATE | NOT NULL | Quarter starting date. |
| 7 | year | INTEGER | NOT NULL | Calendar year. |
| 8 | total_sales | NUMERIC(14,2) | NULL | Total weekly sales. |
| 9 | avg_sales | NUMERIC(12,2) | NULL | Average sales. |
| 10 | num_records | BIGINT | NULL | Count of records aggregated. |
| 11 | sales_52w_ago | NUMERIC(14,2) | NULL | Sales 52 weeks ago (YoY). |
| 12 | sales_1w_ago | NUMERIC(14,2) | NULL | Sales 1 week ago (WoW). |
| 13 | avg_cpi | NUMERIC(10,6) | NULL | Average CPI for the week. |
| 14 | avg_unemployment | NUMERIC(5,3) | NULL | Average unemployment rate. |
| 15 | avg_temperature | NUMERIC(5,2) | NULL | Average temperature. |

### Indexes
```sql
CREATE UNIQUE INDEX idx_plat_trend_unique 
    ON platinum.sales_trend_analysis (store_id, department_id, week_start);
CREATE INDEX idx_plat_trend_week 
    ON platinum.sales_trend_analysis (week_start);
CREATE INDEX idx_plat_trend_month 
    ON platinum.sales_trend_analysis (month_start);
```

### Calculated Fields

**YoY Growth %:**
```sql
(total_sales - sales_52w_ago) / NULLIF(sales_52w_ago, 0) * 100
```

**WoW Growth %:**
```sql
(total_sales - sales_1w_ago) / NULLIF(sales_1w_ago, 0) * 100
```

### Business Rules
1. LAG window functions for time comparisons
2. 52-week lag for YoY (year-over-year)
3. Economic indicators averaged over aggregation period
4. Only current store versions included

### Refresh Schedule
Daily at 3 AM via `REFRESH MATERIALIZED VIEW CONCURRENTLY`

---

# GOLD LAYER

## gold.dim_date

### Description
Date dimension table with complete time hierarchies and calendar attributes.

### Grain
One row per day

### Source
Generated via SQL (2010-2020)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |

# GOLD LAYER

## gold.dim_date

### Description
Date dimension table with complete time hierarchies and calendar attributes.

### Grain
One row per day

### Source
Generated via SQL (2010-2020)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |

# GOLD LAYER

## gold.dim_date

### Description
Date dimension table with complete time hierarchies and calendar attributes.

### Grain
One row per day

### Source
Generated via SQL (2010-2020)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |

# GOLD LAYER

## gold.dim_date

### Description
Date dimension table with complete time hierarchies and calendar attributes.

### Grain
One row per day

### Source
Generated via SQL (2010-2020)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |

# GOLD LAYER

## gold.dim_date

### Description
Date dimension table with complete time hierarchies and calendar attributes.

### Grain
One row per day

### Source
Generated via SQL (2010-2020)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | date_key | INTEGER | NOT NULL | - | PK | Date in YYYYMMDD format. Example: 20100205 |
| 2 | full_date | DATE | NOT NULL | - | UK | Actual date value. |
| 3 | year | INTEGER | NOT NULL | - | - | Calendar year (2010-2020). |
| 4 | year_quarter | VARCHAR(7) | NULL | - | - | Format: 'YYYY-QN'. Example: '2010-Q1' |
| 5 | year_month | VARCHAR(7) | NULL | - | - | Format: 'YYYY-MM'. Example: '2010-02' |
| 6 | year_week | VARCHAR(8) | NULL | - | - | Format: 'YYYY-WNN'. Example: '2010-W05' |
| 7 | month_number | INTEGER | NOT NULL | - | - | Month (1-12). |
| 8 | month_name | VARCHAR(10) | NOT NULL | - | - | Full month name. Example: 'February' |
| 9 | month_abbr | VARCHAR(3) | NOT NULL | - | - | Month abbreviation. Example: 'Feb' |
| 10 | quarter_number | INTEGER | NOT NULL | - | - | Quarter (1-4). |
| 11 | quarter_name | VARCHAR(2) | NULL | - | - | Format: 'QN'. Example: 'Q1' |
| 12 | week_of_year | INTEGER | NOT NULL | - | - | Week of year (1-53). |
| 13 | week_of_month | INTEGER | NULL | - | - | Week of month (1-5). |
| 14 | day_of_month | INTEGER | NOT NULL | - | - | Day (1-31). |
| 15 | day_of_year | INTEGER | NOT NULL | - | - | Day of year (1-366). |
| 16 | day_of_week | INTEGER | NOT NULL | - | - | Day of week (1=Monday, 7=Sunday). |
| 17 | day_name | VARCHAR(10) | NOT NULL | - | - | Full day name. Example: 'Friday' |
| 18 | day_abbr | VARCHAR(3) | NOT NULL | - | - | Day abbreviation. Example: 'Fri' |
| 19 | is_weekend | BOOLEAN | NOT NULL | FALSE | - | TRUE if Saturday or Sunday. |
| 20 | is_holiday | BOOLEAN | NOT NULL | FALSE | - | TRUE if major retail holiday. |
| 21 | holiday_name | VARCHAR(50) | NULL | - | - | Name of holiday. Example: 'Thanksgiving' |
| 22 | is_business_day | BOOLEAN | NOT NULL | TRUE | - | TRUE if not weekend and not holiday. |
| 23 | fiscal_year | INTEGER | NULL | - | - | Fiscal year (starts February for Walmart). |
| 24 | fiscal_quarter | INTEGER | NULL | - | - | Fiscal quarter (1-4). |
| 25 | fiscal_period | INTEGER | NULL | - | - | Fiscal period/month (1-12). |
| 26 | event_name | VARCHAR(100) | NULL | - | - | Special events. Example: 'Black Friday' |
| 27 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.dim_date ADD PRIMARY KEY (date_key);

-- Unique Constraint
ALTER TABLE gold.dim_date ADD CONSTRAINT uq_dim_date_full_date 
    UNIQUE (full_date);

-- Check Constraints
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_month_number 
    CHECK (month_number BETWEEN 1 AND 12);
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_quarter_number 
    CHECK (quarter_number BETWEEN 1 AND 4);
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_week_of_year 
    CHECK (week_of_year BETWEEN 1 AND 53);
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_day_of_month 
    CHECK (day_of_month BETWEEN 1 AND 31);
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_day_of_year 
    CHECK (day_of_year BETWEEN 1 AND 366);
ALTER TABLE gold.dim_date ADD CONSTRAINT chk_day_of_week 
    CHECK (day_of_week BETWEEN 1 AND 7);
```

### Indexes
```sql
CREATE INDEX idx_dim_date_full_date ON gold.dim_date (full_date);
CREATE INDEX idx_dim_date_year_month ON gold.dim_date (year, month_number);
CREATE INDEX idx_dim_date_quarter ON gold.dim_date (year, quarter_number);
CREATE INDEX idx_dim_date_holiday ON gold.dim_date (is_holiday) 
    WHERE is_holiday = TRUE;
```

### Business Rules
1. One row per calendar day
2. date_key format: YYYYMMDD (integer)
3. Week starts on Monday (ISO standard)
4. Fiscal year starts in February (Walmart convention)
5. Holiday calendar includes major US retail holidays
6. Pre-populated for 10 years (2010-2020)

### Time Hierarchies
- Year → Quarter → Month → Week → Day
- Fiscal Year → Fiscal Quarter → Fiscal Period

---

## gold.dim_store

### Description
Store dimension with Type 2 SCD tracking historical changes.

### Grain
One row per store version

### Source
silver.stores

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | store_key | SERIAL | NOT NULL | AUTO | PK | Surrogate key. |
| 2 | store_id | INTEGER | NOT NULL | - | NK | Natural key (1-45). |
| 3 | store_type | VARCHAR(1) | NOT NULL | - | - | Classification: 'A', 'B', 'C'. |
| 4 | store_type_description | VARCHAR(50) | NULL | - | - | Description: 'Superstore', 'Discount Store', 'Neighborhood Market'. |
| 5 | store_size | INTEGER | NOT NULL | - | - | Size in square feet. Must be > 0. |
| 6 | size_category | VARCHAR(20) | NULL | - | - | Category: 'Small', 'Medium', 'Large', 'Extra Large'. |
| 7 | region | VARCHAR(50) | NULL | - | - | Geographic region. Example: 'Northeast' |
| 8 | state | VARCHAR(50) | NULL | - | - | State location. |
| 9 | city | VARCHAR(100) | NULL | - | - | City location. |
| 10 | sales_per_sqft_avg | DECIMAL(10,2) | NULL | - | - | Historical average sales per sq ft. |
| 11 | store_efficiency_rank | INTEGER | NULL | - | - | Efficiency ranking (1-45). |
| 12 | effective_date | DATE | NOT NULL | - | - | Version valid from date. |
| 13 | end_date | DATE | NOT NULL | '9999-12-31' | - | Version valid until date. |
| 14 | is_current | BOOLEAN | NOT NULL | TRUE | - | Current version flag. |
| 15 | version | INTEGER | NOT NULL | 1 | - | Version number. |
| 16 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |
| 17 | updated_at | TIMESTAMP | NOT NULL | NOW() | - | Last update timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.dim_store ADD PRIMARY KEY (store_key);

-- Unique Constraint
ALTER TABLE gold.dim_store ADD CONSTRAINT uq_dim_store_version 
    UNIQUE (store_id, version);

-- Check Constraints
ALTER TABLE gold.dim_store ADD CONSTRAINT chk_dim_store_type 
    CHECK (store_type IN ('A', 'B', 'C'));
ALTER TABLE gold.dim_store ADD CONSTRAINT chk_dim_store_size 
    CHECK (store_size > 0);
```

### Indexes
```sql
CREATE INDEX idx_dim_store_id ON gold.dim_store (store_id);
CREATE INDEX idx_dim_store_current ON gold.dim_store (store_id, is_current) 
    WHERE is_current = TRUE;
CREATE INDEX idx_dim_store_type ON gold.dim_store (store_type);
CREATE INDEX idx_dim_store_eff_date ON gold.dim_store (effective_date);
```

### Business Rules
1. SCD Type 2: Track history of store attribute changes
2. One current version per store (is_current = TRUE)
3. end_date = '9999-12-31' for current records
4. Store type categories: A=Superstore, B=Discount, C=Neighborhood
5. Size categories based on sq ft ranges

### Lookup Logic
```sql
-- For current attributes (most common)
JOIN gold.dim_store ds ON fs.store_key = ds.store_key 
    AND ds.is_current = TRUE

-- For historical attributes at specific date
JOIN gold.dim_store ds ON fs.store_key = ds.store_key 
    AND dd.full_date BETWEEN ds.effective_date AND ds.end_date
```

---

## gold.dim_department

### Description
Department dimension with product hierarchy.

### Grain
One row per department

### Source
silver.sales (distinct departments) + manual enrichment

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | department_key | SERIAL | NOT NULL | AUTO | PK | Surrogate key. |
| 2 | department_id | INTEGER | NOT NULL | - | UK | Natural key (1-99). |
| 3 | department_name | VARCHAR(100) | NULL | - | - | Department name. Example: 'Electronics' |
| 4 | department_category | VARCHAR(50) | NULL | - | - | Category: 'General Merchandise', 'Food', 'Apparel', etc. |
| 5 | department_group | VARCHAR(50) | NULL | - | - | Group: 'Hardlines', 'Softlines', 'Consumables'. |
| 6 | division | VARCHAR(50) | NULL | - | - | Division: 'General Merchandise', 'Grocery', 'Seasonal & Other'. |
| 7 | is_seasonal | BOOLEAN | NOT NULL | FALSE | - | Seasonal department flag. |
| 8 | is_high_margin | BOOLEAN | NOT NULL | FALSE | - | High margin department flag. |
| 9 | avg_margin_pct | DECIMAL(5,2) | NULL | - | - | Average margin percentage. |
| 10 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |
| 11 | updated_at | TIMESTAMP | NOT NULL | NOW() | - | Last update timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.dim_department ADD PRIMARY KEY (department_key);

-- Unique Constraint
ALTER TABLE gold.dim_department ADD CONSTRAINT uq_dim_department_id 
    UNIQUE (department_id);
```

### Indexes
```sql
CREATE INDEX idx_dim_dept_category ON gold.dim_department (department_category);
```

### Business Rules
1. Pre-populated with 99 departments
2. Department categories mapped from department_id ranges
3. Hierarchy: Division → Category → Group → Department
4. Seasonal flag for departments with high seasonal variation

### Category Mapping
- 1-10: Electronics & Home
- 11-20: Apparel & Accessories
- 21-30: General Merchandise
- 31-40: Health & Wellness
- 41-50: Food & Beverage
- 51-60: Fresh Produce
- 61-70: Entertainment
- 71-80: Home Improvement
- 81-90: Seasonal
- 91-99: Other

---

## gold.dim_promotion

### Description
Junk dimension containing unique combinations of markdown types.

### Grain
One row per unique markdown combination

### Source
silver.economic_features (distinct markdown combinations)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | promotion_key | SERIAL | NOT NULL | AUTO | PK | Surrogate key. Special: 0 = "No Promotion" |
| 2 | markdown1 | NUMERIC(12,2) | NOT NULL | 0 | - | MarkDown type 1 amount in USD. |
| 3 | markdown2 | NUMERIC(12,2) | NOT NULL | 0 | - | MarkDown type 2 amount in USD. |
| 4 | markdown3 | NUMERIC(12,2) | NOT NULL | 0 | - | MarkDown type 3 amount in USD. |
| 5 | markdown4 | NUMERIC(12,2) | NOT NULL | 0 | - | MarkDown type 4 amount in USD. |
| 6 | markdown5 | NUMERIC(12,2) | NOT NULL | 0 | - | MarkDown type 5 amount in USD. |
| 7 | total_markdown | NUMERIC(12,2) | NOT NULL | GENERATED | - | Sum of all markdowns. GENERATED COLUMN. |
| 8 | has_markdown1 | BOOLEAN | NOT NULL | GENERATED | - | markdown1 > 0. GENERATED COLUMN. |
| 9 | has_markdown2 | BOOLEAN | NOT NULL | GENERATED | - | markdown2 > 0. GENERATED COLUMN. |
| 10 | has_markdown3 | BOOLEAN | NOT NULL | GENERATED | - | markdown3 > 0. GENERATED COLUMN. |
| 11 | has_markdown4 | BOOLEAN | NOT NULL | GENERATED | - | markdown4 > 0. GENERATED COLUMN. |
| 12 | has_markdown5 | BOOLEAN | NOT NULL | GENERATED | - | markdown5 > 0. GENERATED COLUMN. |
| 13 | num_markdowns | INTEGER | NOT NULL | GENERATED | - | Count of active markdowns. GENERATED COLUMN. |
| 14 | promotion_type | VARCHAR(50) | NULL | - | - | Classification: 'None', 'Light', 'Moderate', 'Heavy'. |
| 15 | promotion_intensity | VARCHAR(20) | NULL | - | - | Intensity: 'None', 'Low', 'Medium', 'High'. |
| 16 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.dim_promotion ADD PRIMARY KEY (promotion_key);

-- Unique Constraint
ALTER TABLE gold.dim_promotion ADD CONSTRAINT uq_dim_promotion 
    UNIQUE (markdown1, markdown2, markdown3, markdown4, markdown5);
```

### Indexes
```sql
CREATE INDEX idx_dim_promo_type ON gold.dim_promotion (promotion_type);
CREATE INDEX idx_dim_promo_intensity ON gold.dim_promotion (promotion_intensity);
```

### Business Rules
1. Junk dimension: Store all unique markdown combinations
2. Special record: promotion_key = 0 for "No Promotion" (0,0,0,0,0)
3. Generated columns automatically calculated on insert/update
4. Promotion type based on total_markdown amount
5. Promotion intensity based on num_markdowns count

### Classification Logic

**Promotion Type:**
- None: total_markdown = 0
- Light: total_markdown < $1,000
- Moderate: total_markdown $1,000 - $4,999
- Heavy: total_markdown >= $5,000

**Promotion Intensity:**
- None: num_markdowns = 0
- Low: num_markdowns = 1-2
- Medium: num_markdowns = 3-4
- High: num_markdowns = 5

---

## gold.dim_economic_factors

### Description
Mini-dimension for economic indicator combinations with bands/categories.

### Grain
One row per unique (rounded) economic indicator combination

### Source
silver.economic_features (distinct combinations)

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | economic_key | SERIAL | NOT NULL | AUTO | PK | Surrogate key. Special: 0 = "Unknown" |
| 2 | temperature | NUMERIC(5,2) | NULL | - | - | Average temperature (°F). Rounded to 0.1. |
| 3 | temperature_band | VARCHAR(20) | NULL | - | - | Band: 'Cold', 'Cool', 'Mild', 'Warm', 'Hot'. |
| 4 | fuel_price | NUMERIC(5,3) | NULL | - | - | Fuel price ($/gallon). Rounded to 0.01. |
| 5 | fuel_price_band | VARCHAR(20) | NULL | - | - | Band: 'Low', 'Medium', 'High', 'Very High'. |
| 6 | cpi | NUMERIC(10,6) | NULL | - | - | Consumer Price Index. Rounded to 0.001. |
| 7 | cpi_category | VARCHAR(20) | NULL | - | - | Category: 'Low Inflation', 'Moderate Inflation', 'High Inflation'. |
| 8 | unemployment | NUMERIC(5,3) | NULL | - | - | Unemployment rate (%). Rounded to 0.01. |
| 9 | unemployment_category | VARCHAR(20) | NULL | - | - | Category: 'Low', 'Medium', 'High'. |
| 10 | economic_condition | VARCHAR(50) | NULL | - | - | Overall condition: 'Peak', 'Growth', 'Recovery', 'Recession'. |
| 11 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.dim_economic_factors ADD PRIMARY KEY (economic_key);

-- Unique Constraint
ALTER TABLE gold.dim_economic_factors ADD CONSTRAINT uq_dim_economic 
    UNIQUE (temperature, fuel_price, cpi, unemployment);
```

### Indexes
```sql
CREATE INDEX idx_dim_econ_condition ON gold.dim_economic_factors (economic_condition);
```

### Business Rules
1. Mini-dimension: Reduce cardinality via rounding
2. Special record: economic_key = 0 for "Unknown"
3. Bands/categories for easier business analysis
4. Economic condition based on unemployment level

### Rounding Strategy
- Temperature: ROUND(X, 1) → 72.3°F
- Fuel Price: ROUND(X, 2) → $2.57
- CPI: ROUND(X, 3) → 211.097
- Unemployment: ROUND(X, 2) → 8.11%

### Band/Category Definitions

**Temperature Bands:**
- Cold: < 32°F
- Cool: 32-50°F
- Mild: 50-70°F
- Warm: 70-85°F
- Hot: > 85°F

**Fuel Price Bands:**
- Low: < $2.50
- Medium: $2.50-$3.50
- High: $3.50-$4.00
- Very High: > $4.00

**CPI Categories:**
- Low Inflation: < 200
- Moderate Inflation: 200-220
- High Inflation: > 220

**Unemployment Categories:**
- Low: < 5%
- Medium: 5-8%
- High: > 8%

**Economic Conditions:**
- Peak: unemployment < 4%
- Growth: unemployment 4-6%
- Recovery: unemployment 6-8%
- Recession: unemployment > 8%

---

## gold.fact_sales

### Description
Central fact table. Weekly sales by store, department with promotion and economic context.

### Grain
One row per store per department per week

### Source
silver.sales + dimension lookups

### Table Structure

| # | Column Name | Data Type | Nullable | Default | PK/FK | Description |
|---|-------------|-----------|----------|---------|-------|-------------|
| 1 | sales_key | BIGSERIAL | NOT NULL | AUTO | PK | Surrogate key. |
| 2 | date_key | INTEGER | NOT NULL | - | FK | Foreign key to dim_date. Format: YYYYMMDD. |
| 3 | store_key | INTEGER | NOT NULL | - | FK | Foreign key to dim_store. |
| 4 | department_key | INTEGER | NOT NULL | - | FK | Foreign key to dim_department. |
| 5 | promotion_key | INTEGER | NOT NULL | - | FK | Foreign key to dim_promotion. Default: 0 (no promo). |
| 6 | economic_key | INTEGER | NOT NULL | - | FK | Foreign key to dim_economic_factors. Default: 0 (unknown). |
| 7 | is_holiday | BOOLEAN | NOT NULL | FALSE | - | Holiday week flag. Degenerate dimension. |
| 8 | weekly_sales | NUMERIC(12,2) | NOT NULL | - | **MEASURE** | Primary measure. Weekly sales amount in USD. |
| 9 | sales_quantity | INTEGER | NULL | 0 | MEASURE | Quantity sold (if available). |
| 10 | sales_vs_ly | NUMERIC(12,2) | NULL | - | CALCULATED | Sales 52 weeks ago (last year). |
| 11 | sales_growth_pct | DECIMAL(5,2) | NULL | - | CALCULATED | Growth % vs last year. Formula: (current - ly) / ly * 100 |
| 12 | created_at | TIMESTAMP | NOT NULL | NOW() | - | Record creation timestamp. |
| 13 | updated_at | TIMESTAMP | NOT NULL | NOW() | - | Last update timestamp. |

### Constraints
```sql
-- Primary Key
ALTER TABLE gold.fact_sales ADD PRIMARY KEY (sales_key);

-- Unique Constraint (Natural Key)
ALTER TABLE gold.fact_sales ADD CONSTRAINT uq_fact_sales 
    UNIQUE (date_key, store_key, department_key);

-- Foreign Keys
ALTER TABLE gold.fact_sales ADD CONSTRAINT fk_fact_date 
    FOREIGN KEY (date_key) REFERENCES gold.dim_date(date_key);
ALTER TABLE gold.fact_sales ADD CONSTRAINT fk_fact_store 
    FOREIGN KEY (store_key) REFERENCES gold.dim_store(store_key);
ALTER TABLE gold.fact_sales ADD CONSTRAINT fk_fact_dept 
    FOREIGN KEY (department_key) REFERENCES gold.dim_department(department_key);
ALTER TABLE gold.fact_sales ADD CONSTRAINT fk_fact_promo 
    FOREIGN KEY (promotion_key) REFERENCES gold.dim_promotion(promotion_key);
ALTER TABLE gold.fact_sales ADD CONSTRAINT fk_fact_econ 
    FOREIGN KEY (economic_key) REFERENCES gold.dim_economic_factors(economic_key);
```

### Indexes
```sql
CREATE INDEX idx_fact_date ON gold.fact_sales (date_key);
CREATE INDEX idx_fact_store ON gold.fact_sales (store_key);
CREATE INDEX idx_fact_dept ON gold.fact_sales (department_key);
CREATE INDEX idx_fact_promo ON gold.fact_sales (promotion_key);
CREATE INDEX idx_fact_econ ON gold.fact_sales (economic_key);
CREATE INDEX idx_fact_composite ON gold.fact_sales (date_key, store_key, department_key);
CREATE INDEX idx_fact_sales_amount ON gold.fact_sales (weekly_sales);
```

### Business Rules
1. Fact table is at Store × Department × Week granularity
2. All foreign keys must reference valid dimension records
3. weekly_sales is the primary additive measure
4. sales_vs_ly and sales_growth_pct are semi-additive (don't SUM across time)
5. is_holiday is degenerate dimension (low cardinality)
6. promotion_key = 0 when no promotion
7. economic_key = 0 when economic data missing

### Measure Types

**Additive Measures:**
- weekly_sales: Can SUM across all dimensions
- sales_quantity: Can SUM across all dimensions

**Semi-Additive Measures:**
- sales_vs_ly: Don't SUM across time, use MAX or AVG
- sales_growth_pct: Don't SUM, use AVG

**Degenerate Dimension:**
- is_holiday: Low cardinality attribute kept in fact

### Load Strategy
```sql
-- Incremental load (daily)
INSERT INTO gold.fact_sales (date_key, store_key, department_key, ...)
SELECT dd.date_key, ds.store_key, de.department_key, ...
FROM silver.sales s
JOIN gold.dim_date dd ON s.date = dd.full_date
JOIN gold.dim_store ds ON s.store_id = ds.store_id AND ds.is_current = TRUE
-- ... other joins
WHERE s.created_at >= CURRENT_DATE - INTERVAL '2 days'
ON CONFLICT (date_key, store_key, department_key)
DO UPDATE SET weekly_sales = EXCLUDED.weekly_sales, updated_at = NOW();
```

---

## APPENDIX A: Data Type Precision Guide

### Numeric Precision Standards

| Data Type | Format | Example | Use Case |
|-----------|--------|---------|----------|
| NUMERIC(5,2) | XXX.XX | 72.31 | Temperature, small decimals |
| NUMERIC(5,3) | XX.XXX | 2.572 | Fuel price, precise decimals |
| NUMERIC(10,6) | XXXX.XXXXXX | 211.096500 | CPI, very precise |
| NUMERIC(12,2) | XXXXXXXXXX.XX | 24924.50 | Sales amounts, money |
| NUMERIC(14,2) | XXXXXXXXXXXX.XX | 1234567.89 | Aggregated sales |

### Date/Time Standards

| Data Type | Format | Example | Use Case |
|-----------|--------|---------|----------|
| DATE | YYYY-MM-DD | 2010-02-05 | Calendar dates |
| INTEGER (date_key) | YYYYMMDD | 20100205 | Date dimension key |
| TIMESTAMP | YYYY-MM-DD HH:MM:SS | 2024-02-08 10:30:00 | Audit timestamps |

### String Length Standards

| Data Type | Max Length | Use Case |
|-----------|-----------|----------|
| VARCHAR(1) | 1 | Store type (A/B/C) |
| VARCHAR(3) | 3 | Day/Month abbreviations |
| VARCHAR(7) | 7 | Year-Quarter, Year-Month |
| VARCHAR(20) | 20 | Category bands |
| VARCHAR(50) | 50 | Names, descriptions |
| VARCHAR(100) | 100 | Longer descriptions |
| VARCHAR(255) | 255 | File paths, long text |

---

## APPENDIX B: Naming Conventions

### Table Naming
- **Format:** `<layer>.<entity>`
- **Examples:** `bronze.sales`, `silver.stores`, `gold.fact_sales`
- **Layer prefixes:** bronze, silver, platinum, gold

### Column Naming
- **Surrogate Keys:** `<entity>_key` (e.g., `store_key`, `sales_key`)
- **Natural Keys:** `<entity>_id` (e.g., `store_id`, `department_id`)
- **Measures:** Descriptive name (e.g., `weekly_sales`, `total_markdown`)
- **Flags:** `is_<condition>` or `has_<condition>` (e.g., `is_holiday`, `has_markdown1`)
- **Dates:** `<purpose>_date` (e.g., `effective_date`, `end_date`)
- **Aggregates:** `<function>_<field>` (e.g., `avg_sales`, `total_sales`)

### Constraint Naming
- **Primary Key:** `pk_<table>`
- **Foreign Key:** `fk_<table>_<referenced_table>`
- **Unique:** `uq_<table>_<columns>`
- **Check:** `chk_<table>_<condition>`

### Index Naming
- **Format:** `idx_<table>_<columns>`
- **Composite:** `idx_<table>_<col1>_<col2>`
- **Partial:** `idx_<table>_<column>_<condition>`

---

## APPENDIX C: Cardinality Reference

| Table | Estimated Rows | Notes |
|-------|---------------|-------|
| bronze.stores | 45 | One per store |
| bronze.features | 8,190 | 45 stores × 182 weeks |
| bronze.sales | 421,570 | 45 stores × 81 depts × 143 weeks (avg) |
| silver.stores | ~100 | 45 stores × 2 versions (avg) |
| silver.economic_features | 8,190 | Same as bronze after cleaning |
| silver.sales | 421,570 | Same as bronze after dedup |
| platinum.promotion_effectiveness | 421,570 | Same grain as silver.sales |
| platinum.sales_trend_analysis | 421,570 | Same grain as silver.sales |
| gold.dim_date | 4,018 | 2010-2020 (10 years) |
| gold.dim_store | ~100 | SCD Type 2 from silver |
| gold.dim_department | 99 | Pre-populated |
| gold.dim_promotion | ~500 | Unique markdown combinations |
| gold.dim_economic_factors | ~1,000 | Unique economic combinations |
| gold.fact_sales | 421,570 | Central fact table |

---

**Document Status:** Final  
**Maintained By:** Data Engineering Team  
**Review Cycle:** Quarterly  
**Last Review:** 2024-02-08