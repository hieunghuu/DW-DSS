# BRONZE LAYER - Raw Data Storage

## 📋 Overview

**Purpose:** Lưu trữ dữ liệu thô từ nguồn CSV, không thay đổi, đảm bảo tính toàn vẹn dữ liệu gốc (lossless replication).

**Principle:** Append-only, immutable, audit trail

**Data Range:** 2010-02-05 to 2012-10-26

**Governance:** Data Engineering Team

---

## 📊 Tables

### 1. bronze.stores

**Description:** Thông tin cửa hàng Walmart

**Source:** stores.csv

**Row Count:** 45 stores

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **store** | INTEGER | NOT NULL | Store identifier (1-45) | 1, 2, 3 |
| **type** | VARCHAR(1) | NOT NULL | Store type classification | 'A', 'B', 'C' |
| **size** | INTEGER | NOT NULL | Store size in square feet | 151315, 202307 |
| ingestion_timestamp | TIMESTAMP | NOT NULL | When data was loaded | 2024-02-08 10:30:00 |
| source_file | VARCHAR(255) | NULL | Source CSV filename | 'stores.csv' |
| row_hash | VARCHAR(64) | NULL | MD5 hash for deduplication | 'a3f5e...' |

**Store Types:**
- **Type A:** Superstore (lớn nhất, đầy đủ dịch vụ)
- **Type B:** Discount Store (trung bình)
- **Type C:** Neighborhood Market (nhỏ nhất, gần khu dân cư)

**Business Rules:**
- Store ID must be unique
- Size must be > 0
- Type must be A, B, or C

**Sample Data:**
```
store | type | size
------|------|-------
1     | A    | 151315
2     | A    | 202307
3     | B    | 37392
4     | A    | 205863
5     | B    | 34875
```

---

### 2. bronze.features

**Description:** Dữ liệu kinh tế và khuyến mãi theo tuần

**Source:** features.csv

**Row Count:** 8,190 rows (45 stores × ~182 weeks)

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **store** | INTEGER | NOT NULL | Store identifier | 1, 2, 3 |
| **date** | DATE | NOT NULL | Week ending date (Friday) | 2010-02-05 |
| temperature | NUMERIC | NULL | Average temperature (°F) | 42.31, 72.5 |
| fuel_price | NUMERIC | NULL | Regional fuel price ($/gallon) | 2.572, 3.458 |
| **markdown1** | NUMERIC | NULL | Promotional markdown type 1 ($) | 0, 1234.56, NaN |
| **markdown2** | NUMERIC | NULL | Promotional markdown type 2 ($) | 0, 567.89, NaN |
| **markdown3** | NUMERIC | NULL | Promotional markdown type 3 ($) | 0, 890.12, NaN |
| **markdown4** | NUMERIC | NULL | Promotional markdown type 4 ($) | 0, 345.67, NaN |
| **markdown5** | NUMERIC | NULL | Promotional markdown type 5 ($) | 0, 123.45, NaN |
| cpi | NUMERIC | NULL | Consumer Price Index | 211.0965, 216.957 |
| unemployment | NUMERIC | NULL | Unemployment rate (%) | 8.106, 7.808 |
| **isholiday** | BOOLEAN | NOT NULL | Holiday week flag | TRUE, FALSE |
| ingestion_timestamp | TIMESTAMP | NOT NULL | When data was loaded | 2024-02-08 10:30:00 |
| source_file | VARCHAR(255) | NULL | Source CSV filename | 'features.csv' |
| row_hash | VARCHAR(64) | NULL | MD5 hash for deduplication | 'b7d2f...' |

**Markdown Types:** (Walmart internal classification)
- MarkDown1-5: Different promotional strategies/categories
- Exact definitions are proprietary to Walmart
- NaN = No promotion that week
- Values represent total markdown amount in dollars

**Holiday Weeks:** (Major US retail holidays)
- Super Bowl (February)
- Labor Day (September)
- Thanksgiving (November)
- Christmas (December)

**Business Rules:**
- (Store, Date) combination must be unique
- CPI must be positive
- Unemployment must be 0-100%
- Fuel_price must be positive
- MarkDowns can be NULL (no promotion)

**Sample Data:**
```
store | date       | temperature | fuel_price | markdown1 | markdown2 | cpi      | unemployment | isholiday
------|------------|-------------|------------|-----------|-----------|----------|--------------|----------
1     | 2010-02-05 | 42.31       | 2.572      | NaN       | NaN       | 211.0965 | 8.106        | FALSE
1     | 2010-02-12 | 38.51       | 2.548      | NaN       | NaN       | 211.2422 | 8.106        | TRUE
1     | 2010-02-19 | 39.93       | 2.514      | NaN       | NaN       | 211.2891 | 8.106        | FALSE
```

---

### 3. bronze.sales

**Description:** Dữ liệu doanh thu hàng tuần theo cửa hàng và phòng ban

**Source:** train.csv

**Row Count:** 421,570 rows (45 stores × 81 depts × ~143 weeks, some missing)

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| **store** | INTEGER | NOT NULL | Store identifier (1-45) | 1, 2, 3 |
| **dept** | INTEGER | NOT NULL | Department identifier (1-99) | 1, 2, 3 |
| **date** | DATE | NOT NULL | Week ending date (Friday) | 2010-02-05 |
| **weekly_sales** | NUMERIC | NOT NULL | Weekly sales amount ($) | 24924.50, -1098.09 |
| isholiday | BOOLEAN | NOT NULL | Holiday week flag | TRUE, FALSE |
| ingestion_timestamp | TIMESTAMP | NOT NULL | When data was loaded | 2024-02-08 10:30:00 |
| source_file | VARCHAR(255) | NULL | Source CSV filename | 'train.csv' |
| row_hash | VARCHAR(64) | NULL | MD5 hash for deduplication | 'c9e4a...' |

**Department Categories:** (Typical Walmart departments)
- 1-10: Electronics, Computers, Cameras
- 11-20: Apparel, Shoes, Jewelry
- 21-30: Home, Furniture, Decor
- 31-40: Health, Beauty, Pharmacy
- 41-50: Food, Snacks, Beverages
- 51-60: Fresh Produce, Bakery, Deli
- 61-70: Entertainment, Books, Music
- 71-80: Sporting Goods, Automotive
- 81-90: Toys, Seasonal items
- 91-99: Other categories

**Weekly Sales:**
- Can be negative (returns exceed sales)
- Measured in USD
- Aggregated at Store × Department × Week level

**Business Rules:**
- (Store, Dept, Date) combination must be unique
- Weekly_sales can be negative
- Date must match with features.date (same weeks)
- isholiday should match with features.isholiday

**Sample Data:**
```
store | dept | date       | weekly_sales | isholiday
------|------|------------|--------------|----------
1     | 1    | 2010-02-05 | 24924.50     | FALSE
1     | 1    | 2010-02-12 | 46039.49     | TRUE
1     | 1    | 2010-02-19 | 41595.55     | FALSE
1     | 2    | 2010-02-05 | 50605.27     | FALSE
1     | 2    | 2010-02-12 | 41188.02     | TRUE
```

---

## 🔄 Data Flow

```
CSV Files (Source)
    ↓
Bronze Tables (Raw Storage)
    ↓
Silver Layer (Cleaning & Transformation)
```

**Load Process:**
1. CSV files placed in `/mnt/project/`
2. Airflow DAG `bronze_ingestion_dag` runs daily at 1 AM
3. Data loaded via Python pandas → PostgreSQL
4. Metadata added (ingestion_timestamp, source_file, row_hash)
5. No transformations, no data quality checks at this layer

---

## 📝 Metadata Columns

All Bronze tables include these audit columns:

| Column | Purpose | Example |
|--------|---------|---------|
| **ingestion_timestamp** | Track when data was loaded | 2024-02-08 10:30:00 |
| **source_file** | Track source CSV file | 'stores.csv' |
| **row_hash** | MD5 hash for deduplication | 'a3f5e7b2c9d1...' |

**Why these columns?**
- **Audit trail:** Know when and from where data came
- **Reprocessing:** Can identify and reload specific batches
- **Deduplication:** Detect duplicate rows across loads
- **Troubleshooting:** Debug data quality issues

---

## ⚠️ Known Data Quality Issues

### Issues in Bronze (NOT fixed, preserved as-is):

1. **NaN values in markdowns:**
   - Many markdown columns contain 'NaN' (Not a Number)
   - Represents weeks with no promotion
   - **Fixed in Silver layer** → converted to 0

2. **Negative sales:**
   - Some weekly_sales values are negative
   - Represents returns > sales that week
   - **Valid business case** → kept as-is

3. **Missing combinations:**
   - Not all Store × Dept × Week combinations exist
   - Some departments not present in all stores
   - Some weeks missing for certain departments
   - **Valid business case** → not all depts in all stores

4. **Date alignment:**
   - All dates are Fridays (week ending)
   - Features and Sales should have matching dates
   - Some mismatches may exist

5. **Data types:**
   - All numeric columns stored as generic NUMERIC
   - **Type casting done in Silver layer**

---

## 🔍 Data Validation Queries

### Check row counts:
```sql
SELECT 'stores' AS table_name, COUNT(*) FROM bronze.stores
UNION ALL
SELECT 'features', COUNT(*) FROM bronze.features
UNION ALL
SELECT 'sales', COUNT(*) FROM bronze.sales;
```

### Check date ranges:
```sql
SELECT 
    MIN(date) AS earliest_date,
    MAX(date) AS latest_date,
    COUNT(DISTINCT date) AS unique_weeks
FROM bronze.sales;
```

### Check for NaN values:
```sql
SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE markdown1 = 'NaN'::numeric) AS nan_markdown1,
    COUNT(*) FILTER (WHERE markdown2 = 'NaN'::numeric) AS nan_markdown2,
    COUNT(*) FILTER (WHERE markdown3 = 'NaN'::numeric) AS nan_markdown3,
    COUNT(*) FILTER (WHERE markdown4 = 'NaN'::numeric) AS nan_markdown4,
    COUNT(*) FILTER (WHERE markdown5 = 'NaN'::numeric) AS nan_markdown5
FROM bronze.features;
```

### Check for negative sales:
```sql
SELECT 
    COUNT(*) AS total_sales_records,
    COUNT(*) FILTER (WHERE weekly_sales < 0) AS negative_sales,
    MIN(weekly_sales) AS min_sales,
    MAX(weekly_sales) AS max_sales,
    AVG(weekly_sales) AS avg_sales
FROM bronze.sales;
```

### Check store types distribution:
```sql
SELECT 
    type,
    COUNT(*) AS num_stores,
    AVG(size)::INTEGER AS avg_size,
    MIN(size) AS min_size,
    MAX(size) AS max_size
FROM bronze.stores
GROUP BY type
ORDER BY type;
```

---

## 📌 Important Notes

1. **Immutability:** Bronze data should NEVER be modified after loading
2. **Append-only:** Only INSERT allowed, no UPDATE/DELETE
3. **Raw format:** Keep exactly as received from source
4. **No transformations:** All cleaning happens in Silver layer
5. **Retention:** Keep all historical loads for audit/replay

---

## 🔗 Related Documentation

- **Silver Layer:** See `SILVER_LAYER_README.md` for cleaned data
- **ETL Pipeline:** See `bronze_ingestion_dag.py` for load process
- **Architecture:** See `DSS_Walmart_Architecture.md` for overall design

---

**Layer:** Bronze (Raw)  
**Last Updated:** 11/02/2026  
**Maintained By:** HieungHuu