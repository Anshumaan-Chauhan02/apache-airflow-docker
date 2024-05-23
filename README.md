# Issues with the Airflow initialization
`airflow db init` is necessary to initialize the Airflow metadata database. Sometimes the issue is that the database initialization is not command is not completed before the scheduler and webserver commands are attempted. Therefore, a more robust method is to ensure the database intiialization using a custom entrypoint script. 

NOTE: Make this script executable by using `chmod +x entrypoint.sh`

# Issues with MySQL initialization
Errors come in with MySQL intiialization, as it does not allow `null` values for the `updated_at` column, that is a `TIMESTAMP`. Therefore, a workaround this is to add a command in the mysql container `--explicit_defaults_for_timestamp=1`, which sets the default value of a timestamp column to 1, and hence we can successfully avoid this issue. 

# Accessing the MySQL server
## Method 1 -  Access MySQL from the Host Machine
As we mapped port number 3307 on the host to port 3306 in the MySQL container, we can connect to MySQL server from the host machine using MySQL client. 

1. Install MySQL Client: If not already installed, install it using `pip install mysqlclient`
2. Connect to MySQL: `mysql -h 127.0.0.1 -P 3307 -u airflow -p`. Enter the password `airflowpassword` when prompted. 

## Method 2 - Access MySQL from the container
1. Open shell in MySQL container: `docker exec -it mysql bash`
2. Connect to MySQL: `mysql -u airflow -p`

# Installing dependencies in Airflow container
## Method 1 - Access the Airflow Container using CLI
1. Connect to the container: `docker exec airflow bash`
2. Install the dependecies using pip: `pip install package-name`

## Method 2 - Use Docker Desktop
1. Open Docker Desktop
2. Go to the containers section and select the `airflow` container
3. Select the `Exec` tab, and it will open a terminal inside the container
4. `pip install package-name`

# PyMySQL for connecting to MySQL database using Python in DAGs
PyMySQL is used for connecting to MySQL server using Python (make sure to have `pymysql` installed on the `airflow` container). 

We utilize the connect() function to establish a connection between database and the host. It requires a set of arguments:
1. host - Host where the database server is located 
2. user - Username to login as 
3. password - Password to use
4. database - Database to use, None to not use a particular one 
5. port - Port where MySQL server is hosted (Default is 3306)

Once the connection is established we can execute the SQL commands and interact with the database. 

# Issue with the Connections
Even though we have created environment variables in the `docker-compose` file, the Airflow is not able to create the metadata to store the details properly. We face issues using the `conn_id` as the table does not contain any information. Therefore, we resorted to manually loading the environment variables and passing them as arguments. 

Naming convention is `AIRFLOW_CONN_{CONN_ID}`, where `CONN_ID` is all uppercase. For example, if the connection id is `my_prod_db`, then the variable name should be `AIRFLOW_CONN_MY_PROD_DB`. 

## Method 1 - JSON format in entrypoint.sh
```
export AIRFLOW_CONN_MYSQL_DEFAULT = '{
    "conn_type": "mysql",
    "login": "airflow",
    "password": "airflowpassword",
    "host": "mysql",
    "schema": "airflow"
}'
```

## Method 2 - Generating a JSON connection representation
To make this JSON generation easier, there is a function in the `Connection` class - `as_json()`. 

```
from airflow.models.connection import Conneciton
c = Connection(
    conn_id = "mysql_default",
    conn_type = "mysql",
    host = "mysql",
    login = "airflow",
    password = "airflowpassword"
    extra = {"extra_param": "this_value"}
)
print(f"AIRFLOW_CONN_{c.conn_id.upper()} = '{c.as_json()}'")
```

## Method 3 - URI format
```
export AIRFLOW_CONN_MY_PROD_DATABASE='my-conn-type://login:password@host:port/schema?param1=val1&param2=val2'
```
For AWS usually, we only require conn-type, login, and password as arguments. 