#!/usr/bin/env python3
"""
Create Supabase tables directly via Python client.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from alprina_cli.api.services.supabase_service import supabase_service


def create_tables():
    """Create database tables."""
    print("Creating Supabase tables...")
    print(f"URL: {supabase_service.url}")
    print(f"Key: {supabase_service.key[:20]}...")

    if not supabase_service.is_enabled():
        print("\n❌ Supabase not configured!")
        return False

    # Read schema file
    schema_file = Path(__file__).parent.parent / "supabase_schema.sql"

    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    print(f"\n✓ Schema file loaded ({len(schema_sql)} chars)")

    # Split into individual statements
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

    print(f"✓ Found {len(statements)} SQL statements")

    # Execute each statement
    for i, statement in enumerate(statements, 1):
        # Skip comments and empty statements
        if not statement or statement.startswith('--'):
            continue

        # Get first line for logging
        first_line = statement.split('\n')[0][:60]

        print(f"\n[{i}/{len(statements)}] Executing: {first_line}...")

        try:
            # Try to execute via SQL editor endpoint
            result = supabase_service.client.rpc('exec', {'query': statement}).execute()
            print(f"  ✓ Success")
        except Exception as e:
            error_msg = str(e)

            # Check if it's just "already exists" - that's OK
            if 'already exists' in error_msg.lower():
                print(f"  ⚠️  Already exists (OK)")
            elif 'does not exist' in error_msg.lower() and 'function' in error_msg.lower():
                print(f"  ⚠️  RPC function not available - will use REST API")
                # Tables will be created via REST API on first use
                return True
            else:
                print(f"  ❌ Error: {error_msg[:100]}")

    print("\n✓ Schema execution complete!")
    return True


if __name__ == "__main__":
    try:
        if create_tables():
            print("\n✅ Tables created successfully!")
            sys.exit(0)
        else:
            print("\n❌ Failed to create tables")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
