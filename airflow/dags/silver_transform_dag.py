from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'hieunghuu',
    'depends_on_past': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'silver_transform_dag',
    default_args=default_args,
    description='Transform Bronze to Silver layer with data quality',
    schedule='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['silver', 'transformation', 'medallion'],
)

# Transform stores to Silver (Type 2 SCD)
transform_silver_stores = SQLExecuteQueryOperator(
    task_id='transform_silver_stores',
    conn_id='walmart_dwh',
    sql='''
        -- Upsert logic with Type 2 SCD
        INSERT INTO silver.stores (store_id, store_type, store_size, effective_date, is_current)
        SELECT DISTINCT ON (store, type, size)
            store AS store_id,
            type AS store_type,
            size AS store_size,
            CURRENT_DATE AS effective_date,
            TRUE AS is_current
        FROM bronze.kaggle_stores
        WHERE ingestion_timestamp >= CURRENT_DATE - INTERVAL '1 day'
        ON CONFLICT (store_id, version) 
        DO UPDATE SET
            store_type = EXCLUDED.store_type,
            store_size = EXCLUDED.store_size,
            updated_at = NOW();
        
        -- Close previous records if changes detected
        UPDATE silver.stores s1
        SET end_date = CURRENT_DATE - INTERVAL '1 day',
            is_current = FALSE
        WHERE s1.is_current = TRUE
        AND EXISTS (
            SELECT 1 FROM silver.stores s2
            WHERE s2.store_id = s1.store_id
            AND s2.effective_date = CURRENT_DATE
            AND s2.store_key != s1.store_key
        );
    ''',
    dag=dag,
)

# Transform features to Silver
transform_silver_features = SQLExecuteQueryOperator(
    task_id='transform_silver_features',
    conn_id='walmart_dwh',
    sql='''
        -- Clean and validate economic features
        WITH latest_features AS (
            SELECT DISTINCT ON (store, date::DATE)
                store AS store_id,
                date::DATE AS date,
                temperature,
                GREATEST(fuel_price, 0) AS fuel_price,  -- No negative prices
                COALESCE(markdown1, 0) AS markdown1,
                COALESCE(markdown2, 0) AS markdown2,
                COALESCE(markdown3, 0) AS markdown3,
                COALESCE(markdown4, 0) AS markdown4,
                COALESCE(markdown5, 0) AS markdown5,
                cpi,
                unemployment,
                isholiday AS is_holiday
            FROM bronze.kaggle_features
            WHERE ingestion_timestamp >= CURRENT_DATE - INTERVAL '1 day'
            AND cpi > 0  -- Data quality: CPI must be positive
            AND unemployment >= 0 AND unemployment <= 100  -- Valid range
            ORDER BY store, date::DATE, ingestion_timestamp DESC
        )
        INSERT INTO silver.economic_features 
        (store_id, date, temperature, fuel_price, markdown1, markdown2, markdown3, 
         markdown4, markdown5, cpi, unemployment, is_holiday)
        SELECT
            store_id,
            date,
            temperature,
            fuel_price,
            markdown1,
            markdown2,
            markdown3,
            markdown4,
            markdown5,
            cpi,
            unemployment,
            is_holiday
        FROM latest_features
        ON CONFLICT (store_id, date) 
        DO UPDATE SET
            temperature = EXCLUDED.temperature,
            fuel_price = EXCLUDED.fuel_price,
            markdown1 = EXCLUDED.markdown1,
            markdown2 = EXCLUDED.markdown2,
            markdown3 = EXCLUDED.markdown3,
            markdown4 = EXCLUDED.markdown4,
            markdown5 = EXCLUDED.markdown5,
            cpi = EXCLUDED.cpi,
            unemployment = EXCLUDED.unemployment,
            is_holiday = EXCLUDED.is_holiday;
    ''',
    dag=dag,
)

# Transform sales to Silver
transform_silver_sales = SQLExecuteQueryOperator(
    task_id='transform_silver_sales',
    conn_id='walmart_dwh',
    sql='''
        -- Clean and deduplicate sales data
        WITH latest_sales AS (
            SELECT DISTINCT ON (store, dept, date::DATE)
                store AS store_id,
                dept AS department_id,
                date::DATE AS date,
                weekly_sales,
                isholiday AS is_holiday
            FROM bronze.kaggle_sales
            WHERE ingestion_timestamp >= CURRENT_DATE - INTERVAL '1 day'
            AND weekly_sales IS NOT NULL  -- No null sales
            ORDER BY store, dept, date::DATE, ingestion_timestamp DESC
        )
        INSERT INTO silver.sales 
        (store_id, department_id, date, weekly_sales, is_holiday)
        SELECT
            store_id,
            department_id,
            date,
            weekly_sales,
            is_holiday
        FROM latest_sales
        ON CONFLICT (store_id, department_id, date) 
        DO UPDATE SET
            weekly_sales = EXCLUDED.weekly_sales,
            is_holiday = EXCLUDED.is_holiday;
    ''',
    dag=dag,
)
handle_null_markdown = SQLExecuteQueryOperator(
    task_id='handle_null_markdown',
    conn_id='walmart_dwh',
    sql='''
        -- Update Silver layer to replace NaN with 0
        UPDATE silver.economic_features
        SET 
            markdown1 = CASE WHEN markdown1 = 'NaN'::numeric THEN 0 ELSE markdown1 END,
            markdown2 = CASE WHEN markdown2 = 'NaN'::numeric THEN 0 ELSE markdown2 END,
            markdown3 = CASE WHEN markdown3 = 'NaN'::numeric THEN 0 ELSE markdown3 END,
            markdown4 = CASE WHEN markdown4 = 'NaN'::numeric THEN 0 ELSE markdown4 END,
            markdown5 = CASE WHEN markdown5 = 'NaN'::numeric THEN 0 ELSE markdown5 END
        WHERE 
            markdown1 = 'NaN'::numeric 
            OR markdown2 = 'NaN'::numeric 
            OR markdown3 = 'NaN'::numeric 
            OR markdown4 = 'NaN'::numeric 
            OR markdown5 = 'NaN'::numeric;

        -- Verify the fix
        SELECT 
            COUNT(*) as total_rows,
            COUNT(*) FILTER (WHERE markdown1 = 'NaN'::numeric) as nan_markdown1,
            COUNT(*) FILTER (WHERE markdown2 = 'NaN'::numeric) as nan_markdown2,
            COUNT(*) FILTER (WHERE markdown3 = 'NaN'::numeric) as nan_markdown3,
            COUNT(*) FILTER (WHERE markdown4 = 'NaN'::numeric) as nan_markdown4,
            COUNT(*) FILTER (WHERE markdown5 = 'NaN'::numeric) as nan_markdown5
        FROM silver.economic_features;
    ''',
    dag=dag,
)
# Task dependencies
transform_silver_stores >> transform_silver_features >> transform_silver_sales >> handle_null_markdown
