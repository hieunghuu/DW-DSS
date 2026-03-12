"""
Gold Star Schema Load DAG
Loads Gold layer Star Schema from Silver/Platinum layers
Schedule: Daily at 4 AM (after Platinum aggregation completes)
"""

from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

dag = DAG(
    'gold_starschema_dag',
    default_args=default_args,
    description='Load Gold layer Star Schema for enterprise reporting',
    schedule='0 4 * * *',  # Daily at 4 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['gold', 'star-schema', 'dwh','medallion'],
)

# ==============================================================================
# TASK 1: Load dim_date (one-time population + ongoing updates)
# ==============================================================================

load_dim_date =  SQLExecuteQueryOperator(
    task_id='load_dim_date',
    conn_id='walmart_dwh',
    sql='''
        -- Insert new dates that don't exist yet
        INSERT INTO gold.dim_date (
            date_key, 
            full_date, 
            year, 
            year_quarter,
            year_month,
            year_week,
            month_number, 
            month_name,
            month_abbr,
            quarter_number,
            quarter_name,
            week_of_year,
            week_of_month,
            day_of_month, 
            day_of_year,
            day_of_week,
            day_name,
            day_abbr,
            is_weekend,
            fiscal_year,
            fiscal_quarter
        )
        SELECT 
            TO_CHAR(s.date, 'YYYYMMDD')::INTEGER AS date_key,
            s.date AS full_date,
            EXTRACT(YEAR FROM s.date)::INTEGER AS year,
            EXTRACT(YEAR FROM s.date) || '-Q' || EXTRACT(QUARTER FROM s.date) AS year_quarter,
            TO_CHAR(s.date, 'YYYY-MM') AS year_month,
            EXTRACT(YEAR FROM s.date) || '-W' || LPAD(EXTRACT(WEEK FROM s.date)::TEXT, 2, '0') AS year_week,
            EXTRACT(MONTH FROM s.date)::INTEGER AS month_number,
            TO_CHAR(s.date, 'Month') AS month_name,
            TO_CHAR(s.date, 'Mon') AS month_abbr,
            EXTRACT(QUARTER FROM s.date)::INTEGER AS quarter_number,
            'Q' || EXTRACT(QUARTER FROM s.date) AS quarter_name,
            EXTRACT(WEEK FROM s.date)::INTEGER AS week_of_year,
            CEIL(EXTRACT(DAY FROM s.date) / 7.0)::INTEGER AS week_of_month,
            EXTRACT(DAY FROM s.date)::INTEGER AS day_of_month,
            EXTRACT(DOY FROM s.date)::INTEGER AS day_of_year,
            EXTRACT(ISODOW FROM s.date)::INTEGER AS day_of_week,
            TO_CHAR(s.date, 'Day') AS day_name,
            TO_CHAR(s.date, 'Dy') AS day_abbr,
            CASE WHEN EXTRACT(ISODOW FROM s.date) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend,
            -- Fiscal year starts in February (for Walmart)
            CASE 
                WHEN EXTRACT(MONTH FROM s.date) >= 2 
                THEN EXTRACT(YEAR FROM s.date)::INTEGER 
                ELSE EXTRACT(YEAR FROM s.date)::INTEGER - 1 
            END AS fiscal_year,
            CASE 
                WHEN EXTRACT(MONTH FROM s.date) IN (2, 3, 4) THEN 1
                WHEN EXTRACT(MONTH FROM s.date) IN (5, 6, 7) THEN 2
                WHEN EXTRACT(MONTH FROM s.date) IN (8, 9, 10) THEN 3
                ELSE 4
            END AS fiscal_quarter
        FROM (
            -- Get all unique dates from silver sales
            SELECT DISTINCT date FROM silver.sales
            UNION
            -- Get all unique dates from silver economic features
            SELECT DISTINCT date FROM silver.economic_features
        ) s
        WHERE NOT EXISTS (
            SELECT 1 FROM gold.dim_date WHERE full_date = s.date
        )
        ORDER BY s.date;
        
        -- Log count
        DO $$
        DECLARE
            new_dates_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO new_dates_count 
            FROM gold.dim_date 
            WHERE created_at >= CURRENT_DATE;
            
            RAISE NOTICE 'Inserted % new dates into dim_date', new_dates_count;
        END $$;
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 2: Update dim_date with holiday flags
# ==============================================================================

update_dim_date_holidays =  SQLExecuteQueryOperator(
    task_id='update_dim_date_holidays',
    conn_id='walmart_dwh',
    sql='''
        -- Mark holidays based on known holiday weeks in the data
        UPDATE gold.dim_date
        SET 
            is_holiday = TRUE,
            holiday_name = CASE
                WHEN month_number = 2 AND day_of_month BETWEEN 10 AND 14 THEN 'Super Bowl'
                WHEN month_number = 9 AND day_of_month BETWEEN 8 AND 12 THEN 'Labor Day'
                WHEN month_number = 11 AND day_of_month BETWEEN 22 AND 28 THEN 'Thanksgiving'
                WHEN month_number = 12 AND day_of_month BETWEEN 24 AND 31 THEN 'Christmas'
                ELSE NULL
            END,
            event_name = CASE
                WHEN month_number = 11 AND day_of_month BETWEEN 24 AND 26 THEN 'Black Friday'
                WHEN month_number = 12 AND day_of_month = 26 THEN 'Boxing Day'
                ELSE NULL
            END
        WHERE is_holiday = FALSE
        AND (
            (month_number = 2 AND day_of_month BETWEEN 10 AND 14) OR
            (month_number = 9 AND day_of_month BETWEEN 8 AND 12) OR
            (month_number = 11 AND day_of_month BETWEEN 22 AND 28) OR
            (month_number = 12 AND day_of_month BETWEEN 24 AND 31)
        );
        
        -- Mark business days (exclude weekends and holidays)
        UPDATE gold.dim_date
        SET is_business_day = NOT (is_weekend OR is_holiday);
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 3: Load dim_store (Type 2 SCD from silver)
# ==============================================================================

load_dim_store =  SQLExecuteQueryOperator(
    task_id='load_dim_store',
    conn_id='walmart_dwh',
    sql='''
        -- Insert new store versions from silver (SCD Type 2)
        INSERT INTO gold.dim_store (
            store_id, 
            store_type, 
            store_type_description,
            store_size, 
            size_category,
            effective_date, 
            end_date, 
            is_current, 
            version
        )
        SELECT 
            ss.store_id,
            ss.store_type,
            CASE ss.store_type
                WHEN 'A' THEN 'Superstore'
                WHEN 'B' THEN 'Discount Store'
                WHEN 'C' THEN 'Neighborhood Market'
            END AS store_type_description,
            ss.store_size,
            CASE 
                WHEN ss.store_size < 50000 THEN 'Small'
                WHEN ss.store_size < 100000 THEN 'Medium'
                WHEN ss.store_size < 150000 THEN 'Large'
                ELSE 'Extra Large'
            END AS size_category,
            ss.effective_date,
            ss.end_date,
            ss.is_current,
            ss.version
        FROM silver.stores ss
        WHERE NOT EXISTS (
            SELECT 1 FROM gold.dim_store ds
            WHERE ds.store_id = ss.store_id 
            AND ds.version = ss.version
        );
        
        -- Log count
        DO $$
        DECLARE
            new_stores_count INTEGER;
        BEGIN
            SELECT COUNT(*) INTO new_stores_count 
            FROM gold.dim_store 
            WHERE created_at >= CURRENT_DATE;
            
            RAISE NOTICE 'Inserted % new store records into dim_store', new_stores_count;
        END $$;
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 4: Load dim_department
# ==============================================================================

load_dim_department =  SQLExecuteQueryOperator(
    task_id='load_dim_department',
    conn_id='walmart_dwh',
    sql='''
        -- Insert new departments discovered in silver.sales
        INSERT INTO gold.dim_department (
            department_id, 
            department_name, 
            department_category,
            department_group,
            division
        )
        SELECT DISTINCT
            s.department_id,
            'Department ' || s.department_id AS department_name,
            CASE 
                WHEN s.department_id <= 10 THEN 'Electronics & Home'
                WHEN s.department_id <= 20 THEN 'Apparel & Accessories'
                WHEN s.department_id <= 30 THEN 'General Merchandise'
                WHEN s.department_id <= 40 THEN 'Health & Wellness'
                WHEN s.department_id <= 50 THEN 'Food & Beverage'
                WHEN s.department_id <= 60 THEN 'Fresh Produce'
                WHEN s.department_id <= 70 THEN 'Entertainment'
                WHEN s.department_id <= 80 THEN 'Home Improvement'
                WHEN s.department_id <= 90 THEN 'Seasonal'
                ELSE 'Other'
            END AS department_category,
            CASE 
                WHEN s.department_id <= 30 THEN 'Hardlines'
                WHEN s.department_id <= 50 THEN 'Softlines'
                ELSE 'Consumables'
            END AS department_group,
            CASE 
                WHEN s.department_id <= 20 THEN 'General Merchandise'
                WHEN s.department_id <= 60 THEN 'Grocery'
                ELSE 'Seasonal & Other'
            END AS division
        FROM silver.sales s
        WHERE NOT EXISTS (
            SELECT 1 FROM gold.dim_department dd
            WHERE dd.department_id = s.department_id
        )
        ORDER BY s.department_id;
        
        -- Update seasonal flag
        UPDATE gold.dim_department
        SET is_seasonal = TRUE
        WHERE department_category IN ('Seasonal', 'Entertainment')
        AND is_seasonal = FALSE;
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 5: Load dim_promotion (Junk Dimension)
# ==============================================================================

load_dim_promotion =  SQLExecuteQueryOperator(
    task_id='load_dim_promotion',
    conn_id='walmart_dwh',
    sql='''
        -- Insert unique markdown combinations
        INSERT INTO gold.dim_promotion (
            markdown1, 
            markdown2, 
            markdown3, 
            markdown4, 
            markdown5,
            promotion_type,
            promotion_intensity
        )
        SELECT DISTINCT
            COALESCE(ROUND(f.markdown1, 2), 0) AS markdown1,
            COALESCE(ROUND(f.markdown2, 2), 0) AS markdown2,
            COALESCE(ROUND(f.markdown3, 2), 0) AS markdown3,
            COALESCE(ROUND(f.markdown4, 2), 0) AS markdown4,
            COALESCE(ROUND(f.markdown5, 2), 0) AS markdown5,
            -- Classify promotion type based on total markdown amount
            CASE 
                WHEN COALESCE(f.markdown1, 0) + COALESCE(f.markdown2, 0) + 
                     COALESCE(f.markdown3, 0) + COALESCE(f.markdown4, 0) + 
                     COALESCE(f.markdown5, 0) = 0 THEN 'None'
                WHEN COALESCE(f.markdown1, 0) + COALESCE(f.markdown2, 0) + 
                     COALESCE(f.markdown3, 0) + COALESCE(f.markdown4, 0) + 
                     COALESCE(f.markdown5, 0) < 1000 THEN 'Light'
                WHEN COALESCE(f.markdown1, 0) + COALESCE(f.markdown2, 0) + 
                     COALESCE(f.markdown3, 0) + COALESCE(f.markdown4, 0) + 
                     COALESCE(f.markdown5, 0) < 5000 THEN 'Moderate'
                ELSE 'Heavy'
            END AS promotion_type,
            -- Classify intensity based on number of active markdowns
            CASE 
                WHEN (CASE WHEN COALESCE(f.markdown1, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown2, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown3, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown4, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown5, 0) > 0 THEN 1 ELSE 0 END) = 0 THEN 'None'
                WHEN (CASE WHEN COALESCE(f.markdown1, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown2, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown3, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown4, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown5, 0) > 0 THEN 1 ELSE 0 END) <= 2 THEN 'Low'
                WHEN (CASE WHEN COALESCE(f.markdown1, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown2, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown3, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown4, 0) > 0 THEN 1 ELSE 0 END +
                      CASE WHEN COALESCE(f.markdown5, 0) > 0 THEN 1 ELSE 0 END) <= 4 THEN 'Medium'
                ELSE 'High'
            END AS promotion_intensity
        FROM silver.economic_features f
        WHERE NOT EXISTS (
            SELECT 1 FROM gold.dim_promotion dp
            WHERE COALESCE(ROUND(f.markdown1, 2), 0) = dp.markdown1
            AND COALESCE(ROUND(f.markdown2, 2), 0) = dp.markdown2
            AND COALESCE(ROUND(f.markdown3, 2), 0) = dp.markdown3
            AND COALESCE(ROUND(f.markdown4, 2), 0) = dp.markdown4
            AND COALESCE(ROUND(f.markdown5, 2), 0) = dp.markdown5
        );
        
        -- Ensure "No Promotion" record exists
        INSERT INTO gold.dim_promotion (
            promotion_key, markdown1, markdown2, markdown3, markdown4, markdown5, 
            promotion_type, promotion_intensity
        )
        VALUES (0, 0, 0, 0, 0, 0, 'None', 'None')
        ON CONFLICT (markdown1, markdown2, markdown3, markdown4, markdown5) DO NOTHING;
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 6: Load dim_economic_factors (Mini-Dimension)
# ==============================================================================

load_dim_economic =  SQLExecuteQueryOperator(
    task_id='load_dim_economic',
    conn_id='walmart_dwh',
    sql='''
        -- Insert unique economic factor combinations (rounded for cardinality control)
        INSERT INTO gold.dim_economic_factors (
            temperature, 
            temperature_band,
            fuel_price, 
            fuel_price_band,
            cpi, 
            cpi_category,
            unemployment, 
            unemployment_category,
            economic_condition
        )
        SELECT DISTINCT
            ROUND(COALESCE(f.temperature, 0), 1) AS temperature,
            CASE 
                WHEN COALESCE(f.temperature, 0) < 32 THEN 'Cold'
                WHEN COALESCE(f.temperature, 0) < 50 THEN 'Cool'
                WHEN COALESCE(f.temperature, 0) < 70 THEN 'Mild'
                WHEN COALESCE(f.temperature, 0) < 85 THEN 'Warm'
                ELSE 'Hot'
            END AS temperature_band,
            ROUND(COALESCE(f.fuel_price, 0), 2) AS fuel_price,
            CASE 
                WHEN COALESCE(f.fuel_price, 0) < 2.5 THEN 'Low'
                WHEN COALESCE(f.fuel_price, 0) < 3.5 THEN 'Medium'
                WHEN COALESCE(f.fuel_price, 0) < 4.0 THEN 'High'
                ELSE 'Very High'
            END AS fuel_price_band,
            ROUND(COALESCE(f.cpi, 1), 3) AS cpi,
            CASE 
                WHEN COALESCE(f.cpi, 0) < 200 THEN 'Low Inflation'
                WHEN COALESCE(f.cpi, 0) < 220 THEN 'Moderate Inflation'
                ELSE 'High Inflation'
            END AS cpi_category,
            ROUND(COALESCE(f.unemployment, 0), 2) AS unemployment,
            CASE 
                WHEN COALESCE(f.unemployment, 0) < 5 THEN 'Low'
                WHEN COALESCE(f.unemployment, 0) < 8 THEN 'Medium'
                ELSE 'High'
            END AS unemployment_category,
            CASE 
                WHEN COALESCE(f.unemployment, 0) >= 8 THEN 'Recession'
                WHEN COALESCE(f.unemployment, 0) >= 6 THEN 'Recovery'
                WHEN COALESCE(f.unemployment, 0) >= 4 THEN 'Growth'
                ELSE 'Peak'
            END AS economic_condition
        FROM silver.economic_features f
        WHERE NOT EXISTS (
            SELECT 1 FROM gold.dim_economic_factors de
            WHERE ROUND(COALESCE(f.temperature, 0), 1) = de.temperature
            AND ROUND(COALESCE(f.fuel_price, 0), 2) = de.fuel_price
            AND ROUND(COALESCE(f.cpi, 1), 3) = de.cpi
            AND ROUND(COALESCE(f.unemployment, 0), 2) = de.unemployment
        );
        
        -- Ensure "Unknown" record exists
        INSERT INTO gold.dim_economic_factors (
            economic_key, temperature, fuel_price, cpi, unemployment, economic_condition
        )
        VALUES (0, 0, 0, 1, 0, 'Unknown')
        ON CONFLICT (temperature, fuel_price, cpi, unemployment) DO NOTHING;
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 7: Load fact_sales (Main Fact Table)
# ==============================================================================

load_fact_sales =  SQLExecuteQueryOperator(
    task_id='load_fact_sales',
    conn_id='walmart_dwh',
    sql='''
        -- Insert/Update fact_sales with latest data from silver
        INSERT INTO gold.fact_sales (
            date_key, 
            store_key, 
            department_key, 
            promotion_key, 
            economic_key,
            weekly_sales, 
            is_holiday
        )
        SELECT 
            dd.date_key,
            ds.store_key,
            de.department_key,
            COALESCE(dp.promotion_key, 0) AS promotion_key,
            COALESCE(ec.economic_key, 0) AS economic_key,
            s.weekly_sales,
            s.is_holiday
        FROM silver.sales s
        -- Join to dim_date
        INNER JOIN gold.dim_date dd ON s.date = dd.full_date
        -- Join to dim_store (current version only)
        INNER JOIN gold.dim_store ds ON s.store_id = ds.store_id 
            AND ds.is_current = TRUE
        -- Join to dim_department
        INNER JOIN gold.dim_department de ON s.department_id = de.department_id
        -- Left join to economic features
        LEFT JOIN silver.economic_features f 
            ON s.store_id = f.store_id AND s.date = f.date
        -- Left join to dim_promotion (match markdown combination)
        LEFT JOIN gold.dim_promotion dp ON 
            COALESCE(ROUND(f.markdown1, 2), 0) = dp.markdown1 AND
            COALESCE(ROUND(f.markdown2, 2), 0) = dp.markdown2 AND
            COALESCE(ROUND(f.markdown3, 2), 0) = dp.markdown3 AND
            COALESCE(ROUND(f.markdown4, 2), 0) = dp.markdown4 AND
            COALESCE(ROUND(f.markdown5, 2), 0) = dp.markdown5
        -- Left join to dim_economic_factors (match rounded values)
        LEFT JOIN gold.dim_economic_factors ec ON 
            ROUND(COALESCE(f.temperature, 0), 1) = ec.temperature AND
            ROUND(COALESCE(f.fuel_price, 0), 2) = ec.fuel_price AND
            ROUND(COALESCE(f.cpi, 1), 3) = ec.cpi AND
            ROUND(COALESCE(f.unemployment, 0), 2) = ec.unemployment
        -- Only insert new records (incremental load)
        WHERE s.created_at >= CURRENT_DATE - INTERVAL '2 days'
        ON CONFLICT (date_key, store_key, department_key) 
        DO UPDATE SET
            weekly_sales = EXCLUDED.weekly_sales,
            is_holiday = EXCLUDED.is_holiday,
            promotion_key = EXCLUDED.promotion_key,
            economic_key = EXCLUDED.economic_key,
            updated_at = NOW();
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 8: Calculate derived measures in fact_sales
# ==============================================================================

calculate_fact_measures =  SQLExecuteQueryOperator(
    task_id='calculate_fact_measures',
    conn_id='walmart_dwh',
    sql='''
        -- Calculate sales_vs_ly (sales vs last year)
        WITH ly_sales AS (
            SELECT
                fs.store_key,
                fs.department_key,
                dd.year,
                dd.week_of_year,
                fs.weekly_sales,
                LAG(fs.weekly_sales, 52) OVER (
                    PARTITION BY fs.store_key, fs.department_key
                    ORDER BY dd.full_date
                ) AS sales_52w_ago
            FROM gold.fact_sales fs
            JOIN gold.dim_date dd ON fs.date_key = dd.date_key
        )
        UPDATE gold.fact_sales fs
        SET
            sales_vs_ly = ly.sales_52w_ago,
            sales_growth_pct = CASE
                WHEN ly.sales_52w_ago IS NOT NULL AND ly.sales_52w_ago > 0
                THEN LEAST(
                    999.99,
                    GREATEST(
                        -999.99,
                        ROUND(
                            ((ly.weekly_sales - ly.sales_52w_ago) / NULLIF(ly.sales_52w_ago, 0) * 100),
                            2
                        )
                    )
                )
                ELSE NULL
            END
        FROM ly_sales ly
        JOIN gold.dim_date dd
        ON dd.year = ly.year
        AND dd.week_of_year = ly.week_of_year
        WHERE fs.store_key = ly.store_key
        AND fs.department_key = ly.department_key
        AND fs.date_key = dd.date_key
        AND fs.updated_at >= CURRENT_DATE - INTERVAL '2 days';
    ''',
    dag=dag,
)

# ==============================================================================
# TASK 9: Refresh statistics for query optimization
# ==============================================================================

def refresh_table_statistics(**context):
    """Run ANALYZE on all gold tables to update query planner statistics"""
    hook = PostgresHook(postgres_conn_id='walmart_dwh')
    
    tables = [
        'gold.dim_date',
        'gold.dim_store',
        'gold.dim_department',
        'gold.dim_promotion',
        'gold.dim_economic_factors',
        'gold.fact_sales'
    ]
    
    for table in tables:
        hook.run(f"ANALYZE {table};")
        print(f"✓ Analyzed {table}")
    
    # Get row counts
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    print("\n=== Gold Layer Row Counts ===")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count:,} rows")
    
    cursor.close()
    conn.close()

refresh_statistics = PythonOperator(
    task_id='refresh_statistics',
    python_callable=refresh_table_statistics,
    dag=dag,
)

# ==============================================================================
# TASK 10: Data quality validation
# ==============================================================================

def validate_star_schema(**context):
    """Validate star schema integrity"""
    hook = PostgresHook(postgres_conn_id='walmart_dwh')
    
    # Check 1: Fact table has no NULL foreign keys
    null_fks = hook.get_first("""
        SELECT COUNT(*) FROM gold.fact_sales 
        WHERE date_key IS NULL 
        OR store_key IS NULL 
        OR department_key IS NULL
    """)[0]
    
    if null_fks > 0:
        raise ValueError(f"Found {null_fks} rows with NULL foreign keys in fact_sales")
    
    # Check 2: All FKs have matching dimension records
    orphan_dates = hook.get_first("""
        SELECT COUNT(*) FROM gold.fact_sales fs 
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_date WHERE date_key = fs.date_key)
    """)[0]
    
    if orphan_dates > 0:
        raise ValueError(f"Found {orphan_dates} orphan date_key references")
    
    orphan_stores = hook.get_first("""
        SELECT COUNT(*) FROM gold.fact_sales fs 
        WHERE NOT EXISTS (SELECT 1 FROM gold.dim_store WHERE store_key = fs.store_key)
    """)[0]
    
    if orphan_stores > 0:
        raise ValueError(f"Found {orphan_stores} orphan store_key references")
    
    # Check 3: Fact table has reasonable sales values
    negative_sales = hook.get_first("""
        SELECT COUNT(*) FROM gold.fact_sales WHERE weekly_sales < 0
    """)[0]
    
    if negative_sales > 0:
        print(f"⚠ Warning: Found {negative_sales} negative sales values")
    
    # Check 4: Verify row count matches silver
    silver_count = hook.get_first("SELECT COUNT(*) FROM silver.sales")[0]
    gold_count = hook.get_first("SELECT COUNT(*) FROM gold.fact_sales")[0]
    
    if abs(gold_count - silver_count) > silver_count * 0.01:  # Allow 1% variance
        raise ValueError(f"Gold fact_sales ({gold_count}) differs significantly from silver.sales ({silver_count})")
    
    print("✅ All star schema validations passed!")
    print(f"   - No NULL foreign keys")
    print(f"   - No orphan references")
    print(f"   - Fact table count: {gold_count:,}")

validate_schema = PythonOperator(
    task_id='validate_star_schema',
    python_callable=validate_star_schema,
    dag=dag,
)

# ==============================================================================
# Task Dependencies
# ==============================================================================

# Dimensions must load before fact
load_dim_date >> update_dim_date_holidays
update_dim_date_holidays >> load_fact_sales

load_dim_store >> load_fact_sales
load_dim_department >> load_fact_sales
load_dim_promotion >> load_fact_sales
load_dim_economic >> load_fact_sales

# Calculate measures after fact load
load_fact_sales >> calculate_fact_measures

# Statistics and validation at the end
calculate_fact_measures >> refresh_statistics >> validate_schema
