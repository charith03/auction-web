import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def verify_postgres():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        return

    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    print(f"Checking PostgreSQL connection...")
    print(f"Host: {hostname}:{port}")
    print(f"User: {username}")
    print(f"Target Database: {database}")

    # Connect to default 'postgres' database to check/create target db
    try:
        con = psycopg2.connect(
            dbname='postgres',
            user=username,
            host=hostname,
            password=password,
            port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{database}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Database '{database}' does not exist. Creating...")
            cur.execute(f"CREATE DATABASE {database}")
            print(f"Database '{database}' created successfully!")
        else:
            print(f"Database '{database}' already exists.")
            
        cur.close()
        con.close()
        
        # Now try connecting to the specific database
        print(f"Verifying connection to '{database}'...")
        con = psycopg2.connect(
            dbname=database,
            user=username,
            host=hostname,
            password=password,
            port=port
        )
        con.close()
        print("SUCCESS: Connection verified and database is ready.")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify_postgres()
