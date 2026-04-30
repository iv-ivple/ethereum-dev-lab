"""
scripts/migrate_keeper_db.py
----------------------------
One-shot migration script: creates the keeper tables in your Postgres database
if they don't already exist.

Uses SQLAlchemy's Base.metadata.create_all() — safe to run multiple times
(CREATE TABLE IF NOT EXISTS under the hood). It will NOT drop or alter
existing tables, so existing data is never touched.

Usage
-----
    python scripts/migrate_keeper_db.py

    # Or point at a different DB without editing .env:
    DATABASE_URL=postgresql://user:pw@host/db python scripts/migrate_keeper_db.py

    # Dry-run: just print the DDL, don't touch the DB:
    python scripts/migrate_keeper_db.py --dry-run

What it creates
---------------
    opportunities   — one row per detected opportunity
    keeper_runs     — one row per bot session
"""

import argparse
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateTable

# Make sure the project root is on the path when running from scripts/
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from keeper.config import config
from keeper.database.models import Base, Opportunity, KeeperRun


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_ddl():
    """Print the SQL that would be executed, without connecting to the DB."""
    # Use a dialect-aware engine with no real connection
    from sqlalchemy.dialects import postgresql
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        print(ddl.strip())
        print(";")
        print()


def run_migration(database_url: str):
    print(f"Connecting to: {database_url!r}")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)

    # Verify connectivity before touching schema
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1, "DB connectivity check failed"
    print("✅ Connection OK")

    # Create tables (idempotent)
    print("Creating tables (if they don't exist)...")
    Base.metadata.create_all(engine)
    print("✅ Tables ready:")

    # Report what exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        if table_name in ("opportunities", "keeper_runs"):
            cols = [c["name"] for c in inspector.get_columns(table_name)]
            print(f"   {table_name}: {cols}")

    engine.dispose()
    print("\n✅ Migration complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Create keeper DB tables")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the DDL SQL without connecting to the database",
    )
    parser.add_argument(
        "--database-url",
        default=config.database_url,
        help="Override DATABASE_URL from .env",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("--- DRY RUN: DDL that would be executed ---\n")
        print_ddl()
        return

    if not args.database_url:
        print("ERROR: DATABASE_URL is not set. Add it to your .env or pass --database-url.")
        sys.exit(1)

    run_migration(args.database_url)


if __name__ == "__main__":
    main()
