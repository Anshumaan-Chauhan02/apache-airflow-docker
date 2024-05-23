#!/bin/bash

# Set MySQL credentials
export MYSQL_USER=airflow
export MYSQL_PASSWORD=airflowpassword

# Function to check if MySQL is ready
function wait_for_mysql() {
  echo "Waiting for MySQL to be available..."
  # Do not put a space after -p otherwise you'll get error
  until mysql -h "mysql" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1" &> /dev/null; do
    echo -n '.'
    sleep 1
  done
  echo "MySQL is up and running!"
}

# Wait for MySQL to be available
wait_for_mysql

# Install required Airflow providers
pip install apache-airflow-providers-amazon
pip install pymysql

# Initialize the Airflow database
echo "Initializing Airflow database..."
airflow db init

# Create Airflow admin user if it does not exist
if ! airflow users list | grep -q admin; then
  echo "Creating Airflow admin user..."
  airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin
fi

# Start the Airflow webserver and scheduler
echo "Starting Airflow webserver and scheduler..."
airflow webserver & airflow scheduler
