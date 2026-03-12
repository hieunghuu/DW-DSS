from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'hieunghuu_analyst',
    'depends_on_past': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'platinum_aggregate_dag',
    default_args=default_args,
    description='Build Platinum layer business domain marts',
    schedule='0 3 * * *',  # Daily at 3 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['platinum', 'aggregation', 'medallion'],
)

# Refresh materialized views
refresh_promotion_effectiveness =  SQLExecuteQueryOperator(
    task_id='refresh_promotion_effectiveness',
    conn_id='walmart_dwh',
    sql='REFRESH MATERIALIZED VIEW CONCURRENTLY platinum.promotion_effectiveness;',
    dag=dag,
)

refresh_sales_trend = SQLExecuteQueryOperator(
    task_id='refresh_sales_trend',
    conn_id='walmart_dwh',
    sql='REFRESH MATERIALIZED VIEW CONCURRENTLY platinum.sales_trend_analysis;',
    dag=dag,
)

# Run in parallel
[refresh_promotion_effectiveness, refresh_sales_trend]