import os
import sys
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from dotenv import load_dotenv
except ImportError:
    print("Required packages not found. Please install requirements.txt first.")
    sys.exit(1)

def create_db():
    load_dotenv()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("Error: DATABASE_URL not found in .env file")
        return

    try:
        result = urlparse(db_url)
        username = result.username
        password = result.password
        db_name = result.path[1:]
        host = result.hostname
        port = result.port or 5432
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        return

    print(f"Connecting to PostgreSQL as user '{username}'...")
    
    try:
        # Connect to 'postgres' system db to create new db
        con = psycopg2.connect(
            dbname='postgres', 
            user=username, 
            host=host, 
            password=password,
            port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{db_name}'...")
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Successfully created database: {db_name}")
        else:
            print(f"Database '{db_name}' already exists.")
            
        cur.close()
        con.close()
        
    except psycopg2.OperationalError as e:
        print(f"\nConnection Error: {e}")
        print("\nPlease check:")
        print("1. Is PostgreSQL running?")
        print("2. Is the password in .env correct?")
        print("3. Is the username 'postgres' correct?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_db()
