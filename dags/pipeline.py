from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook # Interacts with S3 bucket using boto3 library
from airflow.utils.dates import days_ago
import pymysql
import pandas as pd
import json
import urllib3
import os


# ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
# SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Get S3 bucket details from environment variables
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
FILE_KEY = os.getenv('S3_KEY')


def fetch_and_store_data():
    # We utilize BaseHook to get connection details of MySQL server 
    # Connection is a placeholder to store information about different database instances connection information.
    
    # conn_id can be found in the connection table inside the airflow database in MySQL
    # Establishing a connection to MySQL database

    connection = BaseHook.get_connection('mysql_default') 
    
    conn = pymysql.connect(
        host=connection.host,
        user=connection.login,
        password=connection.password,
        database=connection.schema
    )
    
    # conn = pymysql.connect(
    #     host="mysql",
    #     user="airflow",
    #     password="airflowpassword",
    #     database="airflow"
    # )

    # Creates a cursor to execute queries with
    cursor = conn.cursor()

    # Executes a query
    cursor.execute("CREATE TABLE IF NOT EXISTS iss (latitude VARCHAR(255), longitude VARCHAR(255));")

    # Create a PoolManager instance to make requests.
    http = urllib3.PoolManager()

    # Make a request to the API
    response = http.request('GET', 'http://api.open-notify.org/iss-now.json')
    
    # Decoding the response
    response = response.data.decode('utf-8')

    obj = json.loads(response)

    print(obj)
    # Storing values into the table
    cursor.execute(f"INSERT INTO iss VALUES ({obj['iss_position']['latitude']}, {obj['iss_position']['latitude']});")

    # Commit changes to stable storage
    conn.commit()

    # Close the socket 
    conn.close()

def transfer_data_to_s3():
    
    # Establishing connection with MySQL database

    connection = BaseHook.get_connection('mysql_default') 
    
    conn = pymysql.connect(
        host=connection.host,
        user=connection.login,
        password=connection.password,
        database=connection.schema
    )

    # conn = pymysql.connect(
    #     host="mysql",
    #     user="airflow",
    #     password="airflowpassword",
    #     database="airflow"
    # )
    
    # Reading data from the MySQL table
    df = pd.read_sql("SELECT * FROM iss;", conn)

    conn.close()

    # Establishing a connection with the S3 bucket
    s3_hook = S3Hook(aws_conn_id='aws_default')

    # s3_hook = S3Hook(aws_conn_id = 'aws_default', \
    #                  region_name = 'us-east-1', \
    #                  aws_access_key_id = ACCESS_KEY, \
    #                  aws_secret_access_key = SECRET_KEY)

    # Creating a csv file for the data
    df.to_csv('/tmp/iss.csv', index=False)

    # Loads local file to S3
    s3_hook.load_file(
        filename = "/tmp/iss.csv",
        key=FILE_KEY,
        bucket_name=BUCKET_NAME,
        replace=True
        )


default_args = {
    'start_date': days_ago(1), # kept the start date one day before
}

# Declaring a DAG 
pipeline_dag = DAG(
    dag_id='pipeline',
    default_args=default_args,
    schedule_interval='*/5 * * * *', # will run every 5 minutes (CRON job)
    catchup=False, # won't catchup to the missed schedules from the start date
)

# Passing the DAG into the operator instance
fetch_and_store = PythonOperator(
    task_id='fetch_and_store_data',
    python_callable=fetch_and_store_data,
    dag = pipeline_dag # DAG getting atatched to the task id (can be done only once)
)

transfer_data = PythonOperator(
    task_id='transfer_data_to_s3',
    python_callable=transfer_data_to_s3,
    dag = pipeline_dag
)

# Calling the Operator
fetch_and_store >> transfer_data
