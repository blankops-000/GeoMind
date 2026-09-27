import sys
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine, Base
import app.db.models  # Register models


def init_db():
    print(f"Connecting to database at {settings.DATABASE_URL}...")
    with engine.connect() as conn:
        print("Ensuring extension 'postgis' is created...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    print("Creating database tables...")
    Base.metadata.create_all(engine)

    print("Successfully created/verified tables:")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f"  - {table_name}")

    print("Database initialization complete.")


if __name__ == "__main__":
    try:
        init_db()
        sys.exit(0)
    except Exception as e:
        print(f"Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)
