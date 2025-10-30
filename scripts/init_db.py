import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with required tables"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'twitter_sentiment'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute the initialization SQL
        with open('database/init.sql', 'r') as f:
            init_sql = f.read()
            cursor.execute(init_sql)
        
        logger.info("✅ Database initialized successfully")
        
        # Test the connection by listing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        logger.info("📊 Available tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database()
