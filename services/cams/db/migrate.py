"""
Database migration script for CAMS.

This script sets up the initial database schema for the Central Agent Mapping Service.
"""
import os
import asyncio
import asyncpg
from pathlib import Path
from typing import Optional

# Get database connection parameters from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'database': os.getenv('DB_NAME', 'postgres')  # Connect to default database first
}

SCHEMA_FILE = Path(__file__).parent.parent / 'create_cams_table.sql'

def read_sql_file(file_path: Path) -> str:
    """Read the SQL file and return its content."""
    with open(file_path, 'r') as f:
        return f.read()

async def database_exists(conn: asyncpg.Connection, dbname: str) -> bool:
    """Check if a database exists."""
    result = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", dbname
    )
    return result is not None

async def create_database() -> None:
    """Create the database if it doesn't exist."""
    # Connect to the default database
    conn = await asyncpg.connect(**{**DB_CONFIG, 'database': 'postgres'})

    try:
        db_name = os.getenv('DB_NAME', 'cams')

        # Check if database exists
        exists = await database_exists(conn, db_name)

        if not exists:
            print(f"Creating database: {db_name}")
            # Create the database
            await conn.execute(f'CREATE DATABASE {db_name}')
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")

    except Exception as e:
        print(f"Error creating database: {e}")
        raise
    finally:
        await conn.close()

async def run_migrations() -> None:
    """Run database migrations."""
    # First, ensure the database exists
    await create_database()

    # Now connect to the target database
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Read and execute the schema SQL
        sql = read_sql_file(SCHEMA_FILE)

        # Split into individual statements and execute them
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        async with conn.transaction():
            for stmt in statements:
                if stmt.upper().startswith('COMMENT'):
                    # Skip COMMENT statements as they might reference objects that don't exist yet
                    continue
                try:
                    await conn.execute(stmt)
                except Exception as e:
                    print(f"Error executing statement: {stmt[:100]}...")
                    raise

        print("Database schema created/updated successfully.")

    except Exception as e:
        print(f"Error running migrations: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())
