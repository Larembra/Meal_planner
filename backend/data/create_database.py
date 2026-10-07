"""Create the Meal_planner PostgreSQL database from the bundled snapshot.

The script validates the complete SQL snapshot in a temporary database before
creating the requested target. Connection settings use PGHOST, PGPORT, PGUSER,
PGPASSWORD and PGDATABASE. Requires psycopg2-binary; the PostgreSQL server must
have the pgcrypto and pgvector extensions available.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

import psycopg2
from psycopg2 import sql

DATA_DIR = Path(__file__).resolve().parent
SNAPSHOT = DATA_DIR / "seed.sql"


def create_database(admin, name: str) -> None:
    with admin.cursor() as cursor:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


def drop_database(admin, name: str) -> None:
    with admin.cursor() as cursor:
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))


def load_snapshot(connection_settings: dict[str, object], database: str, snapshot: str) -> None:
    connection = psycopg2.connect(**connection_settings, dbname=database)
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(snapshot)
    finally:
        connection.close()


def main() -> None:
    database = os.getenv("PGDATABASE", "Meal_planner_test")
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "postgres")
    connection_settings: dict[str, object] = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
    }

    if not SNAPSHOT.is_file():
        raise FileNotFoundError(f"Database snapshot not found: {SNAPSHOT}")
    snapshot = SNAPSHOT.read_text(encoding="utf-8-sig")
    extensions = set(
        re.findall(
            r"(?im)^\s*CREATE\s+EXTENSION\s+IF\s+NOT\s+EXISTS\s+([a-zA-Z0-9_]+)",
            snapshot,
        )
    )
    if not extensions:
        raise RuntimeError("No CREATE EXTENSION statements found in the SQL snapshot.")

    admin = psycopg2.connect(**connection_settings, dbname="postgres")
    admin.autocommit = True
    try:
        with admin.cursor() as cursor:
            cursor.execute("SELECT name FROM pg_available_extensions")
            available = {row[0] for row in cursor.fetchall()}
            missing = extensions - available
            if missing:
                raise RuntimeError(
                    "PostgreSQL is missing required extension package(s): "
                    + ", ".join(sorted(missing))
                    + ". Install the server-side extension package(s) first."
                )

            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if cursor.fetchone():
                raise RuntimeError(
                    f"Database {database!r} already exists. Choose another PGDATABASE; "
                    "the existing database was not changed."
                )

            # CREATE EXTENSION is tested transactionally before any database is made.
            cursor.execute("BEGIN")
            try:
                for extension in sorted(extensions):
                    cursor.execute(
                        sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                            sql.Identifier(extension)
                        )
                    )
                if "vector" in extensions:
                    cursor.execute("SELECT '[0, 1]'::vector(2)")
                cursor.execute("ROLLBACK")
            except Exception as exc:
                cursor.execute("ROLLBACK")
                raise RuntimeError(
                    "PostgreSQL extension preflight failed; the target database "
                    "was not created. Check server-side extensions and permissions."
                ) from exc

        # Apply every DDL statement and row in a throwaway database first. This
        # catches schema ordering, data, extension, and index errors in advance.
        preflight_database = f"meal_planner_preflight_{uuid.uuid4().hex}"
        create_database(admin, preflight_database)
        try:
            load_snapshot(connection_settings, preflight_database, snapshot)
        except Exception as exc:
            drop_database(admin, preflight_database)
            raise RuntimeError(
                "Snapshot preflight failed; the requested target database was not created."
            ) from exc
        else:
            drop_database(admin, preflight_database)

        # Recheck in case another process created the target during preflight.
        with admin.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
            if cursor.fetchone():
                raise RuntimeError(
                    f"Database {database!r} appeared during preflight. "
                    "It was left unchanged."
                )
        create_database(admin, database)
    finally:
        admin.close()

    try:
        load_snapshot(connection_settings, database, snapshot)
    except Exception:
        # This database was created by this run and remains empty after transaction rollback.
        cleanup = psycopg2.connect(**connection_settings, dbname="postgres")
        cleanup.autocommit = True
        try:
            drop_database(cleanup, database)
        finally:
            cleanup.close()
        raise

    print(f"Created {database!r} from {SNAPSHOT.name}.")


if __name__ == "__main__":
    main()
