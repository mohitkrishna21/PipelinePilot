
import sqlite3
from contextlib import closing


def read_pipeline(db_path: str) -> list[dict]:
    with closing(
        sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    ) as conn:

        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT
                id,
                company,
                role,
                tier,
                date_applied,
                current_stage,
                last_activity_date,
                next_action,
                next_action_date,
                contact_name,
                source,
                notes
            FROM applications
            ORDER BY last_activity_date DESC
        """)

        rows = [dict(r) for r in cursor.fetchall()]

    return rows
