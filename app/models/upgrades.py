"""Changes for databases created before a model changed.

`db.create_all()` and CREATE TABLE IF NOT EXISTS never alter a table that already exists,
so every column added to a model after the first release is listed here. The statements are
written into database/psupulse.sql (scripts/export_schema.py) and run by scripts/init_db.py.
They are MariaDB syntax (XAMPP) and safe to run more than once.
"""

SCHEMA_UPGRADES = [
    "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(100) NULL AFTER unit_id;",
]
