# backend/app/inspect_db.py
import sqlite3, json, os
DB = os.path.join(os.path.dirname(__file__), "db.sqlite")

def main():
    print("DB path:", DB)
    if not os.path.exists(DB):
        print("File DB tidak ditemukan.")
        return

    con = sqlite3.connect(DB)
    cur = con.cursor()

    print("\n--- Tables ---")
    for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        print(" -", r[0])

    print("\n--- Query history sample (latest 50) ---")
    try:
        rows = cur.execute(
            "SELECT id, user_id, query, created_at, results FROM query_history ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        print(f"Found {len(rows)} rows in query_history")
        for r in rows:
            id_, uid, q, created_at, results = r
            # try pretty results
            try:
                parsed = json.loads(results) if results else []
            except Exception:
                parsed = results[:200] if results else ""
            print(f"\nid={id_} user_id={uid} created_at={created_at}")
            print(" query:", q)
            print(" results (first 2):", parsed[:2] if isinstance(parsed, list) else parsed)
    except Exception as e:
        print("Could not query query_history:", e)

    con.close()

if __name__ == "__main__":
    main()
