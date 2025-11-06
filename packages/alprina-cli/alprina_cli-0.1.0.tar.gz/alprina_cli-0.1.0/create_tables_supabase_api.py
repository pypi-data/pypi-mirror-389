"""
Create database tables using Supabase REST API.
This bypasses DNS/connection issues by using HTTP.
"""

import os
import requests
from loguru import logger

# SQL to create all tables
CREATE_TABLES_SQL = """
-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free' NOT NULL,
    polar_customer_id VARCHAR(255) UNIQUE,
    polar_subscription_id VARCHAR(255) UNIQUE,
    subscription_status VARCHAR(50) DEFAULT 'inactive',
    subscription_started_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_polar_customer ON users(polar_customer_id);

-- 2. Usage Tracking Table
CREATE TABLE IF NOT EXISTS usage_tracking (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month VARCHAR(7) NOT NULL,
    scans_count INTEGER DEFAULT 0 NOT NULL,
    scans_limit INTEGER,
    files_scanned_total INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    api_calls_count INTEGER DEFAULT 0 NOT NULL,
    api_calls_limit INTEGER,
    parallel_scans_count INTEGER DEFAULT 0,
    sequential_scans_count INTEGER DEFAULT 0,
    coordinated_chains_count INTEGER DEFAULT 0,
    last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month)
);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_user ON usage_tracking(user_id);

-- 3. Scan History Table
CREATE TABLE IF NOT EXISTS scan_history (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scan_type VARCHAR(100) NOT NULL,
    agent_used VARCHAR(100) NOT NULL,
    target TEXT,
    files_count INTEGER DEFAULT 0,
    findings_count INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    high_findings INTEGER DEFAULT 0,
    medium_findings INTEGER DEFAULT 0,
    low_findings INTEGER DEFAULT 0,
    workflow_mode VARCHAR(50),
    duration_seconds FLOAT,
    status VARCHAR(50) DEFAULT 'completed',
    report_path TEXT,
    report_format VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_history_user ON scan_history(user_id);

-- 4. API Keys Table
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) DEFAULT 'API Key',
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);

-- 5. Polar Webhooks Table
CREATE TABLE IF NOT EXISTS polar_webhooks (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    event_type VARCHAR(100) NOT NULL,
    polar_event_id VARCHAR(255) UNIQUE,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE NOT NULL,
    processed_at TIMESTAMP,
    error_message TEXT,
    polar_customer_id VARCHAR(255),
    polar_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_polar_webhooks_processed ON polar_webhooks(processed);
"""

def create_tables_via_api():
    """Create tables using Supabase REST API."""

    # Get Supabase URL and key
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL or SUPABASE_KEY not set")
        return False

    # Extract project ref from URL
    # URL format: postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
    try:
        import re
        match = re.search(r'db\.([a-z]+)\.supabase\.co', supabase_url)
        if match:
            project_ref = match.group(1)
            api_url = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec_sql"
        else:
            logger.error("Could not extract project ref from SUPABASE_URL")
            return False

    except Exception as e:
        logger.error(f"Failed to parse SUPABASE_URL: {e}")
        return False

    logger.info(f"🔌 Connecting to Supabase project: {project_ref}")

    # Make API request to execute SQL
    try:
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        # Note: Supabase doesn't have a direct SQL execution endpoint in REST API
        # We'll need to use the PostgREST interface or SQL Editor
        logger.warning("⚠️  Cannot create tables via REST API")
        logger.info("\n📋 Please create tables manually:")
        logger.info("1. Go to https://app.supabase.com")
        logger.info("2. Select your project")
        logger.info("3. Go to SQL Editor")
        logger.info("4. Copy and run the SQL from SUPABASE-SETUP-GUIDE.md")
        logger.info("\nOr use Supabase CLI:")
        logger.info(f"  supabase db push")

        return False

    except Exception as e:
        logger.error(f"Failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Supabase Table Creation")
    logger.info("="*60)

    create_tables_via_api()

    logger.info("\n📝 SQL Script Available:")
    logger.info("   See SUPABASE-SETUP-GUIDE.md for complete SQL")
    logger.info("\n✅ Recommended: Use Supabase SQL Editor in dashboard")
