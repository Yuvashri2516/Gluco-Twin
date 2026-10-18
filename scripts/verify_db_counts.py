"""
verify_db_counts.py - Read-Only Database Safety Verification
"""
import sqlite3

def check_db(path):
    print(f"=== DB: {path} ===")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    print("Tables:", sorted(tables))
    counts = {}
    for t in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        counts[t] = cursor.fetchone()[0]
        print(f"  {t}: {counts[t]} rows")
    conn.close()
    return counts

print("ACTIVE DATABASE:")
active = check_db("backend/glucotwin.db")
print("\nPHASE 0 BACKUP:")
backup = check_db("backend/glucotwin.db.backup_phase0_20261018")
