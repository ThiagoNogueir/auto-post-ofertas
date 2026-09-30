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

    print("\n=== TESTE DE MODELOS GROQ ===")
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        for model in ['llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'qwen/qwen3.8-27b']:
            try:
                t0 = time.time()
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Classifique em 1 palavra entre [Casa, Tech, Moda]: Fritadeira Air Fryer Philco"}],
                    temperature=0,
                    max_tokens=10
                )
                print(f"Modelo {model}: {resp.choices[0].message.content.strip()} em {round(time.time() - t0, 3)}s")
            except Exception as me:
                print(f"Modelo {model} erro: {me}")
    except Exception as e:
        print("Erro geral:", e)

if __name__ == '__main__':
    check_latest()
