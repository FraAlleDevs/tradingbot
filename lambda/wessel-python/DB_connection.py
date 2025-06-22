import psycopg2
import os
from dotenv import load_dotenv, dotenv_values

conn = None

# function to establish connection with postgres DB.
def get_postgres_connection():

    conn = None
    load_dotenv()

    print('Connecting to the PostgreSQL database...')
    try:
        conn = psycopg2.connect (
            host = os.getenv("DB_HOST"),
            dbname = os.getenv("DB_NAME"),
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            port = os.getenv("DB_PORT")
        )
        
        if conn is None:
            print('Connection to the DB failed.')
            return
        print('Connection to the DB was SUCCESFUL.')
        return conn

    
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
