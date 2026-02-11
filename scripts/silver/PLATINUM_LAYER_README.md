# SILVER LAYER - Cleaned & Conformed Data

## 📋 Overview

**Purpose:** Dữ liệu đã được làm sạch, chuẩn hóa, và validate. Source-aligned clean datasets sẵn sàng cho phân tích.

**Principle:** Clean, conform, validate, deduplicate

**Transformations:** Data quality rules, type casting, null handling, business rules

**Governance:** Source System Teams / Data Engineering

---

## 📊 Tables

### 1. silver.stores (SCD Type 2)

**Description:** Store dimension với Type 2 Slowly Changing Dimension để track historical changes

**Source:** bronze.stores

**Row Count:** ~100 rows (45 stores × ~2 versions average)

**Transformations from Bronze:**
- ✅ Add surrogate key (store_key)
- ✅ Rename columns (store → store_id, type → store_type, size → store_size)
- ✅ Add SCD Type 2 columns (effective_date, end_date, is_current, version)
- ✅ Type validation (store_type IN ('A', 'B', 'C'))
- ✅ Size validation (store_size > 0)

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **store_key** | SERIAL | NOT NULL (PK) | Surrogate key (unique per version) | 1, 2, 3 |
| **store_id** | INTEGER | NOT NULL | Natural key (business identifier) | 1, 2, 3 |
| **store_type** | VARCHAR(1) | NOT NULL | Store classification | 'A', 'B', 'C' |
| **store_size** | INTEGER | NOT NULL | Size in square feet | 151315 |
| **effective_date** | DATE | NOT NULL | Version valid from | 2010-02-05 |
| **end_date** | DATE | NOT NULL | Version valid until | 2011-06-30 or 9999-12-31 |
| **is_current** | BOOLEAN | NOT NULL | Current version flag | TRUE/FALSE |
| **version** | INTEGER | NOT NULL | Version number | 1, 2, 3 |
| created_at | TIMESTAMP | NOT NULL | Record creation time | 2024-02-08 10:30:00 |
| updated_at | TIMESTAMP | NOT NULL | Last update time | 2024-02-08 10:30:00 |

**Constraints:**
- PRIMARY KEY: store_key
- UNIQUE: (store_id, version)
- CHECK: store_type IN ('A', 'B', 'C')
- CHECK: store_size > 0

**SCD Type 2 Example:**
```
store_key | store_id | store_type | store_size | effective_date | end_date   | is_current | version
----------|----------|------------|------------|----------------|------------|------------|--------
1         | 1        | A          | 151315     | 2010-02-05     | 2011-06-30 | FALSE      | 1
2         | 1        | A          | 180000     | 2011-07-01     | 9999-12-31 | TRUE       | 2
3         | 2        | A          | 202307     | 2010-02-05     | 9999-12-31 | TRUE       | 1
```

**Business Rules:**
- One current version per store (is_current = TRUE)
- Versions are ordered by effective_date
- New version created when store_type or store_size changes
- end_date = '9999-12-31' for current records

**Query Current Stores:**
```sql
SELECT * FROM silver.stores WHERE is_current = TRUE;
```

---

### 2. silver.economic_features

**Description:** Economic indicators và promotional markdowns, cleaned và validated

**Source:** bronze.features

**Row Count:** 8,190 rows (same as Bronze after deduplication)

**Transformations from Bronze:**
- ✅ Add surrogate key (feature_id)
- ✅ Rename columns (store → store_id)
- ✅ **Convert NaN to 0 for all markdowns**
- ✅ Type casting (temperature → NUMERIC(5,2), fuel_price → NUMERIC(5,3))
- ✅ Data validation (fuel_price >= 0, cpi > 0, unemployment 0-100%)
- ✅ Null handling (markdown NULL → 0)

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **feature_id** | SERIAL | NOT NULL (PK) | Surrogate key | 1, 2, 3 |
| **store_id** | INTEGER | NOT NULL | Store identifier | 1, 2, 3 |
| **date** | DATE | NOT NULL | Week ending date | 2010-02-05 |
| temperature | NUMERIC(5,2) | NULL | Average temperature (°F) | 42.31 |
| fuel_price | NUMERIC(5,3) | NULL | Fuel price ($/gallon), validated >= 0 | 2.572 |
| **markdown1** | NUMERIC(12,2) | NOT NULL | Markdown type 1 (NaN → 0) | 0.00, 1234.56 |
| **markdown2** | NUMERIC(12,2) | NOT NULL | Markdown type 2 (NaN → 0) | 0.00, 567.89 |
| **markdown3** | NUMERIC(12,2) | NOT NULL | Markdown type 3 (NaN → 0) | 0.00, 890.12 |
| **markdown4** | NUMERIC(12,2) | NOT NULL | Markdown type 4 (NaN → 0) | 0.00, 345.67 |
| **markdown5** | NUMERIC(12,2) | NOT NULL | Markdown type 5 (NaN → 0) | 0.00, 123.45 |
| cpi | NUMERIC(10,6) | NULL | Consumer Price Index, validated > 0 | 211.096500 |
| unemployment | NUMERIC(5,3) | NULL | Unemployment %, validated 0-100 | 8.106 |
| is_holiday | BOOLEAN | NOT NULL | Holiday week flag | TRUE/FALSE |
| created_at | TIMESTAMP | NOT NULL | Record creation time | 2024-02-08 10:30:00 |

**Constraints:**
- PRIMARY KEY: feature_id
- UNIQUE: (store_id, date)
- CHECK: fuel_price >= 0
- CHECK: cpi > 0
- CHECK: unemployment >= 0 AND unemployment <= 100

**Key Transformations:**

1. **NaN Handling:**
```sql
-- Bronze: markdown1 = 'NaN'
-- Silver: markdown1 = 0.00
COALESCE(NULLIF(markdown1, 'NaN'::numeric), 0)
```

2. **Type Precision:**
```sql
-- Bronze: temperature = NUMERIC (generic)
-- Silver: temperature = NUMERIC(5,2) (e.g., 72.31)
```

3. **Data Validation:**
```sql
-- Reject rows where CPI <= 0 (invalid)
-- Reject rows where unemployment > 100 (invalid)
-- Replace negative fuel_price with NULL
```

**Sample Data:**
```
feature_id | store_id | date       | temperature | fuel_price | markdown1 | markdown2 | cpi      | unemployment | is_holiday
-----------|----------|------------|-------------|------------|-----------|-----------|----------|--------------|----------
1          | 1        | 2010-02-05 | 42.31       | 2.572      | 0.00      | 0.00      | 211.0965 | 8.106        | FALSE
2          | 1        | 2010-02-12 | 38.51       | 2.548      | 0.00      | 0.00      | 211.2422 | 8.106        | TRUE
3          | 1        | 2010-02-19 | 39.93       | 2.514      | 0.00      | 0.00      | 211.2891 | 8.106        | FALSE
```

---

### 3. silver.sales

**Description:** Weekly sales data, cleaned và deduplicated

**Source:** bronze.sales

**Row Count:** ~421,570 rows (after deduplication)

**Transformations from Bronze:**
- ✅ Add surrogate key (sales_id)
- ✅ Rename columns (store → store_id, dept → department_id)
- ✅ Type casting (weekly_sales → NUMERIC(12,2))
- ✅ Deduplication on (store_id, department_id, date)
- ✅ Remove rows with NULL weekly_sales
- ✅ Keep negative sales (valid returns case)

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **sales_id** | BIGSERIAL | NOT NULL (PK) | Surrogate key | 1, 2, 3 |
| **store_id** | INTEGER | NOT NULL | Store identifier | 1, 2, 3 |
| **department_id** | INTEGER | NOT NULL | Department identifier | 1, 2, 3 |
| **date** | DATE | NOT NULL | Week ending date | 2010-02-05 |
| **weekly_sales** | NUMERIC(12,2) | NOT NULL | Weekly sales amount ($) | 24924.50 |
| is_holiday | BOOLEAN | NOT NULL | Holiday week flag | TRUE/FALSE |
| created_at | TIMESTAMP | NOT NULL | Record creation time | 2024-02-08 10:30:00 |

**Constraints:**
- PRIMARY KEY: sales_id
- UNIQUE: (store_id, department_id, date)

**Business Rules:**
- weekly_sales can be negative (returns exceed sales)
- weekly_sales cannot be NULL
- (store_id, department_id, date) must be unique
- date should exist in economic_features for same store

**Negative Sales Examples:**
```sql
SELECT store_id, department_id, date, weekly_sales
FROM silver.sales
WHERE weekly_sales < 0
ORDER BY weekly_sales
LIMIT 5;

-- Result:
store_id | department_id | date       | weekly_sales
---------|---------------|------------|-------------
33       | 47            | 2011-12-30 | -4988.94
14       | 13            | 2010-11-05 | -2955.50
```

**Sample Data:**
```
sales_id | store_id | department_id | date       | weekly_sales | is_holiday
---------|----------|---------------|------------|--------------|----------
1        | 1        | 1             | 2010-02-05 | 24924.50     | FALSE
2        | 1        | 1             | 2010-02-12 | 46039.49     | TRUE
3        | 1        | 1             | 2010-02-19 | 41595.55     | FALSE
4        | 1        | 2             | 2010-02-05 | 50605.27     | FALSE
```

---

## 🔄 Data Quality Rules

### Applied in Silver Layer:

#### 1. **Null Handling**
- ✅ Markdown NaN → 0
- ✅ Markdown NULL → 0
- ✅ Temperature NULL → keep NULL (optional field)
- ✅ Fuel_price NULL → keep NULL (optional field)

#### 2. **Data Validation**
- ✅ CPI must be > 0
- ✅ Unemployment must be 0-100%
- ✅ Fuel_price must be >= 0
- ✅ Store_size must be > 0
- ✅ Weekly_sales cannot be NULL

#### 3. **Type Casting**
```sql
Bronze              → Silver
------                ------
NUMERIC (generic)   → NUMERIC(5,2)    [temperature]
NUMERIC (generic)   → NUMERIC(5,3)    [fuel_price]
NUMERIC (generic)   → NUMERIC(12,2)   [markdowns]
NUMERIC (generic)   → NUMERIC(10,6)   [cpi]
NUMERIC (generic)   → NUMERIC(5,3)    [unemployment]
```

#### 4. **Deduplication**
```sql
-- If duplicate (store_id, department_id, date) exists
-- Keep the one with latest ingestion_timestamp
-- Or take MAX(weekly_sales) if same timestamp
```

#### 5. **Referential Checks**
```sql
-- sales.store_id must exist in stores.store_id
-- economic_features.store_id must exist in stores.store_id
-- sales.date should match economic_features.date for same store
```

---

## 📊 Data Quality Metrics

### Check Data Quality After Transformation:

```sql
-- 1. Check for NaN values (should be 0)
SELECT 
    COUNT(*) FILTER (WHERE markdown1 = 'NaN'::numeric) AS nan_count_md1,
    COUNT(*) FILTER (WHERE markdown2 = 'NaN'::numeric) AS nan_count_md2,
    COUNT(*) FILTER (WHERE markdown3 = 'NaN'::numeric) AS nan_count_md3,
    COUNT(*) FILTER (WHERE markdown4 = 'NaN'::numeric) AS nan_count_md4,
    COUNT(*) FILTER (WHERE markdown5 = 'NaN'::numeric) AS nan_count_md5
FROM silver.economic_features;
-- Expected: all 0

-- 2. Check for NULL weekly_sales (should be 0)
SELECT COUNT(*) 
FROM silver.sales 
WHERE weekly_sales IS NULL;
-- Expected: 0

-- 3. Check referential integrity
SELECT COUNT(*) 
FROM silver.sales s
WHERE NOT EXISTS (
    SELECT 1 FROM silver.stores st 
    WHERE st.store_id = s.store_id 
    AND st.is_current = TRUE
);
-- Expected: 0

-- 4. Check invalid CPI
SELECT COUNT(*) 
FROM silver.economic_features 
WHERE cpi <= 0;
-- Expected: 0

-- 5. Check invalid unemployment
SELECT COUNT(*) 
FROM silver.economic_features 
WHERE unemployment < 0 OR unemployment > 100;
-- Expected: 0
```

---

## 🔄 Transformation Logic

### From Bronze to Silver:

#### stores:
```sql
INSERT INTO silver.stores (store_id, store_type, store_size, effective_date, is_current)
SELECT DISTINCT
    store AS store_id,
    type AS store_type,
    size AS store_size,
    '2010-02-05'::DATE AS effective_date,
    TRUE AS is_current
FROM bronze.stores
WHERE type IN ('A', 'B', 'C')
AND size > 0;
```

#### economic_features:
```sql
INSERT INTO silver.economic_features (
    store_id, date, temperature, fuel_price, 
    markdown1, markdown2, markdown3, markdown4, markdown5,
    cpi, unemployment, is_holiday
)
SELECT 
    store AS store_id,
    date::DATE,
    temperature::NUMERIC(5,2),
    GREATEST(fuel_price::NUMERIC(5,3), 0),
    COALESCE(NULLIF(markdown1, 'NaN'::numeric), 0)::NUMERIC(12,2),
    COALESCE(NULLIF(markdown2, 'NaN'::numeric), 0)::NUMERIC(12,2),
    COALESCE(NULLIF(markdown3, 'NaN'::numeric), 0)::NUMERIC(12,2),
    COALESCE(NULLIF(markdown4, 'NaN'::numeric), 0)::NUMERIC(12,2),
    COALESCE(NULLIF(markdown5, 'NaN'::numeric), 0)::NUMERIC(12,2),
    cpi::NUMERIC(10,6),
    unemployment::NUMERIC(5,3),
    isholiday AS is_holiday
FROM bronze.features
WHERE cpi > 0
AND unemployment >= 0 AND unemployment <= 100;
```

#### sales:
```sql
INSERT INTO silver.sales (
    store_id, department_id, date, weekly_sales, is_holiday
)
SELECT 
    store AS store_id,
    dept AS department_id,
    date::DATE,
    weekly_sales::NUMERIC(12,2),
    isholiday AS is_holiday
FROM bronze.sales
WHERE weekly_sales IS NOT NULL
ON CONFLICT (store_id, department_id, date) DO UPDATE
SET weekly_sales = EXCLUDED.weekly_sales;
```

---

## 📈 Usage Examples

### Query 1: Get current store information
```sql
SELECT 
    store_id,
    store_type,
    store_size,
    effective_date
FROM silver.stores
WHERE is_current = TRUE
ORDER BY store_id;
```

### Query 2: Get all economic data for a specific week
```sql
SELECT 
    store_id,
    temperature,
    fuel_price,
    markdown1 + markdown2 + markdown3 + markdown4 + markdown5 AS total_markdown,
    cpi,
    unemployment,
    is_holiday
FROM silver.economic_features
WHERE date = '2011-12-30'
ORDER BY store_id;
```

### Query 3: Find top selling departments in holiday weeks
```sql
SELECT 
    department_id,
    SUM(weekly_sales) AS total_holiday_sales,
    COUNT(*) AS num_weeks
FROM silver.sales
WHERE is_holiday = TRUE
GROUP BY department_id
ORDER BY total_holiday_sales DESC
LIMIT 10;
```

### Query 4: Join sales with economic features
```sql
SELECT 
    s.store_id,
    s.department_id,
    s.date,
    s.weekly_sales,
    f.temperature,
    f.fuel_price,
    f.markdown1,
    f.cpi,
    f.unemployment
FROM silver.sales s
LEFT JOIN silver.economic_features f 
    ON s.store_id = f.store_id 
    AND s.date = f.date
WHERE s.date BETWEEN '2011-01-01' AND '2011-12-31'
ORDER BY s.date, s.store_id, s.department_id;
```

---

## ⚠️ Known Issues & Limitations

### 1. **Date Mismatches**
- Some sales records may not have matching economic_features
- Some stores may have missing weeks
- **Resolution:** Use LEFT JOIN when combining tables

### 2. **Department Coverage**
- Not all departments exist in all stores
- Some departments may have gaps in weekly data
- **Resolution:** Normal business case, handled in analysis

### 3. **Negative Sales**
- Approximately 1% of records have negative sales
- Represents returns > sales that week
- **Resolution:** Valid data, keep for analysis

### 4. **Temperature/Fuel Price NULLs**
- Some records missing temperature or fuel price
- Regional data may not be available for all stores/weeks
- **Resolution:** Keep NULL, use COALESCE in queries if needed

---

## 🔗 Downstream Usage

Silver tables are used by:

1. **Platinum Layer:** Pre-aggregated business domain marts
2. **Gold Layer:** Star schema fact and dimension tables
3. **Ad-hoc Analysis:** Data scientists and analysts
4. **Data Quality Reporting:** Monitoring dashboards

---

## 📌 Best Practices

1. **Always filter current stores:**
```sql
JOIN silver.stores st ON ... AND st.is_current = TRUE
```

2. **Handle NULLs in aggregations:**
```sql
COALESCE(SUM(markdown1), 0) AS total_markdown1
```

3. **Check date alignment:**
```sql
-- Verify sales and features have matching dates
SELECT DISTINCT s.date 
FROM silver.sales s
WHERE NOT EXISTS (
    SELECT 1 FROM silver.economic_features f 
    WHERE f.store_id = s.store_id AND f.date = s.date
);
```

4. **Use proper data types in queries:**
```sql
-- Don't do string comparison on numerics
-- Good: WHERE cpi > 200
-- Bad:  WHERE cpi::TEXT > '200'
```

---

## 🔗 Related Documentation

- **Bronze Layer:** See `BRONZE_LAYER_README.md` for raw data
- **Platinum Layer:** See `PLATINUM_LAYER_README.md` for business marts
- **Gold Layer:** See `GOLD_LAYER_README.md` for star schema
- **ETL Pipeline:** See `/airflow/dags` for transformation logic

---

**Layer:** Silver (Cleaned)  
**Last Updated:** 11/02/2026  
**Maintained By:** hieunghuu
**SLA:** Data refreshed daily at 2 AM