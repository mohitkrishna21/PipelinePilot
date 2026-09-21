import sqlite3
import os


def create_schema(conn):
    cursor = conn.cursor()
    create_table_sql = """CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('tier1','tier2','tier3','stretch')),
    date_applied TEXT NOT NULL,
    current_stage TEXT NOT NULL CHECK (current_stage IN ('applied','oa','phone_screen','onsite','offer','rejected','withdrawn')),
    last_activity_date TEXT NOT NULL,
    next_action TEXT,
    next_action_date TEXT,
    contact_name TEXT,
    contact_email TEXT,
    source TEXT,
    notes TEXT)"""

    cursor.execute(create_table_sql)
    conn.commit()

def seed_demo_data(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications")
    cursor.execute(
    "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
    "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
    "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    ("Google", "Applied AI Engineer", "tier1", "2026-09-16", "applied",
     "2026-09-16", None, None, None, None, "career_page", None)
    )
    cursor.execute(
        "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
        "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
        "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Amazon", "AI Engineer", "tier1", "2026-09-01", "applied",
         "2026-09-01", None, None, None, None, "career_page", None)
    )
    cursor.execute(
        "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
        "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
        "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Databricks", "ML Engineer", "tier2", "2026-08-22", "phone_screen",
        "2026-08-27", None, None, None, None, "career_page", None)
    )
    cursor.execute(
        "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
        "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
        "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Snowflake", "AI Engineer", "tier2", "2026-08-27", "onsite",
        "2026-09-13", None, None, None, None, "career_page", None)
    )
    cursor.execute(
        "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
        "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
        "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("NVIDIA", "AI Engineer", "tier1", "2026-08-17", "offer",
        "2026-09-11", None, None, None, None, "career_page", None)
    )
    cursor.execute(
        "INSERT INTO applications (company, role, tier, date_applied, current_stage, "
        "last_activity_date, next_action, next_action_date, contact_name, contact_email, "
        "source, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Adobe", "ML Engineer", "tier3", "2026-08-27", "rejected",
        "2026-09-06", None, None, None, None, "career_page", None)
    )
    conn.commit()

if __name__ == "__main__":
    
    script_folder = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_folder, "demo_pipeline.db")

    conn = sqlite3.connect(db_path)
    create_schema(conn)
    seed_demo_data(conn)
    conn.close()


    
