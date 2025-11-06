#!/usr/bin/env python3
"""
Run database migrations for Alprina.
"""

import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration(migration_file: Path):
    """Run a single migration file."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    client = create_client(url, key)

    print(f"🔄 Running migration: {migration_file.name}")

    try:
        sql = migration_file.read_text()

        # Split SQL into individual statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]

        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"  Executing statement {i}/{len(statements)}...", end=' ')
                # Execute via RPC call
                client.rpc('exec_sql', {'sql': statement}).execute()
                print("✓")

        print(f"✅ Migration {migration_file.name} completed successfully\n")

    except Exception as e:
        print(f"\n❌ Error running migration: {e}")
        sys.exit(1)


def main():
    """Run all pending migrations."""
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get all .sql files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("ℹ️  No migrations found")
        return

    print(f"Found {len(migration_files)} migration(s)\n")

    for migration_file in migration_files:
        run_migration(migration_file)

    print("✅ All migrations completed successfully!")


if __name__ == "__main__":
    main()
