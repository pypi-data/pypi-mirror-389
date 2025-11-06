"""
Create database tables from SQLAlchemy models.

This script creates all tables defined in the database models for Polar integration.
"""

import os
from sqlalchemy import create_engine, text
from loguru import logger

# Import models
from alprina_cli.api.models.database import Base

def create_tables():
    """Create all database tables."""

    # Get database URL from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        logger.error("SUPABASE_URL environment variable not set")
        logger.info("Please set SUPABASE_URL to your Supabase PostgreSQL connection string")
        logger.info("Example: postgresql://user:password@host:5432/database")
        return False

    try:
        # Create engine
        logger.info(f"Connecting to database...")
        engine = create_engine(supabase_url)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL: {version[:50]}...")

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)

        logger.success("✅ All tables created successfully!")

        # List created tables
        logger.info("\nCreated tables:")
        logger.info("  - users")
        logger.info("  - usage_tracking")
        logger.info("  - scan_history")
        logger.info("  - api_keys")
        logger.info("  - polar_webhooks")

        return True

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def verify_tables():
    """Verify tables were created."""

    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        return

    try:
        engine = create_engine(supabase_url)

        with engine.connect() as conn:
            # Query table names
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'usage_tracking', 'scan_history', 'api_keys', 'polar_webhooks')
                ORDER BY table_name
            """))

            tables = [row[0] for row in result]

            if tables:
                logger.info("\n✅ Verified tables exist:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.warning("\n⚠️  No tables found. They may already exist or creation failed.")

    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Creating Alprina Database Tables")
    logger.info("="*60 + "\n")

    if create_tables():
        verify_tables()
        logger.info("\n🎉 Database setup complete!")
    else:
        logger.error("\n❌ Database setup failed")
        logger.info("\nPlease ensure:")
        logger.info("1. SUPABASE_URL environment variable is set")
        logger.info("2. Database connection is working")
        logger.info("3. You have permissions to create tables")
