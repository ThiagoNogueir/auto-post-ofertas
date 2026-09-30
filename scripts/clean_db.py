"""
Database & Scraper Reset Script.
Clears processed deals history and resets scraper pagination to Page 1.
Ensures fresh deals are processed and posted with the new AI semantic categorization.
"""

import os
import json
import sqlite3

def reset_db_and_scrapers(db_path: str, state_path: str):
    print("=" * 60)
    print("RESETTING DEALS DATABASE & SCRAPER STATE")
    print("=" * 60)

    # 1. Reset Deals in SQLite
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Check if deals table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deals'")
        if cur.fetchone():
            count_before = cur.execute("SELECT count(*) FROM deals").fetchone()[0]
            cur.execute("DELETE FROM deals")
            conn.commit()
            cur.execute("VACUUM")
            print(f"[OK] Cleared {count_before} old deals from 'deals' table in: {db_path}")
        else:
            print(f"[INFO] Table 'deals' not found in: {db_path}")
            
        conn.close()
    else:
        print(f"[WARNING] Database not found at: {db_path}")

    # 2. Reset Scraper Pagination State
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"[OK] Reset scraper pagination state in: {state_path}")
    except Exception as e:
        print(f"[ERROR] Could not reset scraper state: {e}")

    print("=" * 60)
    print("DATABASE & SCRAPER RESET COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(base_dir, 'data', 'deals.db')
    state_file = os.path.join(base_dir, 'data', 'scraper_state.json')
    reset_db_and_scrapers(db_file, state_file)
