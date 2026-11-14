"""One-time helper for Module 7 Step 3: drop the 4 Module 7 tables so they are recreated with the new columns.
Touches ONLY Module 7 tables (they hold no real data yet). Modules 1-6 are not affected.
Run from the backend folder:  python -m scripts.reset_career_tables
"""
from sqlalchemy import inspect, text

from app.db.database import engine

TABLES = ["career_actions", "interview_prep_items", "opportunity_matches", "career_plans"]  # FK-safe order

if __name__ == "__main__":
    existing = set(inspect(engine).get_table_names())
    with engine.begin() as conn:
        for t in TABLES:
            if t in existing:
                conn.execute(text(f"DROP TABLE {t} CASCADE"))
                print(f"dropped {t}")
    print("Done. Restart the backend: the tables are recreated on startup.")
