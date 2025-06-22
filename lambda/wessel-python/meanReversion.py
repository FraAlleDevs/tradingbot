import psycopg2
from DB_connection import get_postgres_connection

def meanReversion():
    
    conn = get_postgres_connection()
    if conn is None:
        print("Cannot query without DB connection")
        return

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM report_card;")
        response = cur.fetchall()
        
        print(f"ID | created_at | algorithm_version | start_date | end_date | performance")
    
        for row in response:
            id, created_at, algorithm_version, start_date, end_date, performance = row
            print(f"{id} | {created_at} | {algorithm_version} | {start_date} | {end_date} | {performance}")
        
        # Close the connection
        cur.close()
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

if __name__ == "__main__":
    meanReversion()        

