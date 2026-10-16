"""Create the database (MySQL via XAMPP) and all tables, upgrade tables from older versions,
and add the default offices and a first admin account.

Usage:  python scripts/init_db.py            create what is missing
        python scripts/init_db.py --reset    drop every table first (destroys data!)
"""
import argparse
import os

import _bootstrap  # noqa: F401
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db
from app.models import Unit, User
from app.models.unit import DEFAULT_OFFICES
from app.models.upgrades import SCHEMA_UPGRADES


def ensure_mysql_database(uri):
    url = make_url(uri)
    if not url.drivername.startswith("mysql"):
        return
    import pymysql

    conn = pymysql.connect(host=url.host or "127.0.0.1", port=url.port or 3306,
                           user=url.username, password=url.password or "")
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{url.database}' is ready.")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    args = parser.parse_args()

    app = create_app()
    ensure_mysql_database(app.config["SQLALCHEMY_DATABASE_URI"])
    with app.app_context():
        if args.reset:
            db.drop_all()
            print("All tables dropped.")
        db.create_all()
        print("Tables created.")
        if db.engine.dialect.name == "mysql":
            for statement in SCHEMA_UPGRADES:
                db.session.execute(text(statement))
            db.session.commit()
            print("Tables upgraded.")

        added = [Unit(code=code, name=name, unit_type="office") for code, name in DEFAULT_OFFICES
                 if not Unit.query.filter_by(code=code).first()]
        if added:
            db.session.add_all(added)
            db.session.commit()
            print(f"Added {len(added)} default office(s).")

        username = os.getenv("ADMIN_USERNAME", "admin")
        if not User.query.filter_by(username=username).first():
            admin = User(username=username, full_name="System Administrator", role="admin")
            admin.set_password(os.getenv("ADMIN_PASSWORD", "admin12345"))
            db.session.add(admin)
            db.session.commit()
            print(f"Admin account '{username}' created. Change its password after signing in.")


if __name__ == "__main__":
    main()
