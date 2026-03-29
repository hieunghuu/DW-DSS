from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import hashlib

default_args = {
    'owner': 'hieunghuu',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bronze_ingestion_dag',
    default_args=default_args,
    description='Ingest raw CSV files into Bronze layer',
    schedule='0 1 * * *',  # Daily at 1 AM
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['bronze', 'ingestion', 'medallion'],
)

stores_table='bronze.kaggle_stores'
features_table='bronze.kaggle_features'
sales_table='bronze.kaggle_sales'
def ingest_stores(**context):
    """Ingest stores.csv into stores table"""
    hook = PostgresHook(postgres_conn_id='walmart_dwh')
    
    # Read CSV
    df = pd.read_csv('/opt/airflow/dataset/stores.csv')
    
    # Add metadata
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = 'stores.csv'
    df['row_hash'] = df.apply(
        lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), 
        axis=1
    )
    
    # Insert into PostgreSQL
    hook.insert_rows(
        table=stores_table,
        rows=df.values.tolist(),
        target_fields=df.columns.tolist(),
        replace=False,
        commit_every=1000
    )
    
    print(f"Ingested {len(df)} rows into stores")

def ingest_features(**context):
    """Ingest features.csv into features table"""
    hook = PostgresHook(postgres_conn_id='walmart_dwh')
    
    df = pd.read_csv('/opt/airflow/dataset/features.csv')
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = 'features.csv'
    df['row_hash'] = df.apply(
        lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), 
        axis=1
    )
    
    hook.insert_rows(
        table=features_table,
        rows=df.values.tolist(),
        target_fields=df.columns.tolist(),
        replace=False,
        commit_every=1000
    )
    
    print(f"Ingested {len(df)} rows into features")

def ingest_sales(**context):
    """Ingest train.csv into sales table"""
    hook = PostgresHook(postgres_conn_id='walmart_dwh')
    
    # Read in chunks for large file (421K rows)
    chunk_size = 10000
    total_rows = 0
    
    for chunk in pd.read_csv('/opt/airflow/dataset/train.csv', chunksize=chunk_size):
        chunk['ingestion_timestamp'] = datetime.now()
        chunk['source_file'] = 'train.csv'
        chunk['row_hash'] = chunk.apply(
            lambda row: hashlib.md5(str(row.to_dict()).encode()).hexdigest(), 
            axis=1
        )
        
        hook.insert_rows(
            table=sales_table,
            rows=chunk.values.tolist(),
            target_fields=chunk.columns.tolist(),
            replace=False,
            commit_every=1000
        )
        
        total_rows += len(chunk)
    
    print(f"Ingested {total_rows} rows into sales")

# Define tasks
task_ingest_stores = PythonOperator(
    task_id='ingest_stores',
    python_callable=ingest_stores,
    dag=dag,
)

task_ingest_features = PythonOperator(
    task_id='ingest_features',
    python_callable=ingest_features,
    dag=dag,
)

task_ingest_sales = PythonOperator(
    task_id='ingest_sales',
    python_callable=ingest_sales,
    dag=dag,
)

# Can run in parallel
[task_ingest_stores, task_ingest_features, task_ingest_sales]