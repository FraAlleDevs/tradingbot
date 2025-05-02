import psycopg2
import os
from dotenv import load_dotenv, dotenv_values

conn = None
load_dotenv()
try:
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    conn = psycopg2.connect(
        host = 'localhost',
        dbname = 'bitcoin_db',
        user = 'root',
        password = os.getenv("POSTGRES_PASSWORD"),
        port = 5432
    )
    
    # Creating a cursor with name cur.
    cur = conn.cursor()
    print('Connected to the PostgreSQL database')
    
    # Execute a query:
    # To display the PostgreSQL 
    # database server version
    cur.execute('SELECT * from btc_historical')
    print(cur.fetchall())
    
    # Close the connection
    cur.close()
    
except(Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    if conn is not None:
        conn.close()
        print('Database connection closed.')
