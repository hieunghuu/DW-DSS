
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
