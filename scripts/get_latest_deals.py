import sqlite3
import time
import os
from datetime import datetime

def check_latest():
    conn = sqlite3.connect('/app/data/deals.db')
    c = conn.cursor()
    print("=== ÚLTIMO PRODUTO ENVIADO EM CADA GRUPO / CATEGORIA ===")
    c.execute("""
        SELECT d.category, d.sent_at, d.price, d.title, d.affiliate_url
        FROM deals d
        INNER JOIN (
            SELECT category, MAX(sent_at) as max_sent
            FROM deals
            GROUP BY category
        ) m ON d.category = m.category AND d.sent_at = m.max_sent
        ORDER BY d.sent_at DESC
    """)
    rows = c.fetchall()
    for r in rows:
        print(f"[{r[0]}] {r[1]} | R$ {r[2]} | {r[3]}")
        print(f"  Link: {r[4]}\n")

    print("=== TOTAL GERAL DE OFERTAS POR CATEGORIA ===")
    c.execute("SELECT category, count(*) FROM deals GROUP BY category ORDER BY count(*) DESC")
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}")

    print("\n=== MODELOS DISPONÍVEIS NA GROQ ===")
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        models = [m.id for m in client.models.list().data]
        print("Modelos Groq:", models)
    except Exception as e:
        print("Erro listando modelos:", e)

if __name__ == '__main__':
    check_latest()
