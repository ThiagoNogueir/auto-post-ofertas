import sqlite3

def check_latest():
    conn = sqlite3.connect('/app/data/deals.db')
    c = conn.cursor()
    print("--- PRODUTOS COM 'IPHONE' OU 'APPLE' NO BANCO ---")
    c.execute("""
        SELECT id, category, price, sent_at, title, affiliate_url 
        FROM deals 
        WHERE LOWER(title) LIKE '%iphone%' OR LOWER(title) LIKE '%apple%'
        ORDER BY id DESC LIMIT 20
    """)
    rows = c.fetchall()
    for r in rows:
        print(f"ID: {r[0]} | Cat: {r[1]} | R$ {r[2]} | {r[3]}\nTítulo: {r[4]}\nLink: {r[5]}\n")
    if not rows:
        print("Nenhum produto encontrado com 'iphone' ou 'apple'.")

if __name__ == '__main__':
    check_latest()
