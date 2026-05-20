import sys, io, psycopg2, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = psycopg2.connect(
    "postgresql://ranking_record_user:0DMQwPfdf8oIA0ttdtlUS6QkNqYU6Ure"
    "@dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com/ranking_record"
)
cur = conn.cursor()
cur.execute("SELECT id, username, password, location, words_mastered, words_learned, learned_ids, mastered_ids FROM users ORDER BY id;")
rows = cur.fetchall()
print(f"共 {len(rows)} 个用户\n")
for r in rows:
    learned = json.loads(r[6] or "[]")
    mastered = json.loads(r[7] or "[]")
    print(f"ID={r[0]}  用户名={r[1]}  密码={r[2]}  位置={r[3] or '(空)'}")
    print(f"  words_mastered={r[4]}  words_learned={r[5]}")
    print(f"  learned_ids({len(learned)}个): {learned[:10]}{'...' if len(learned)>10 else ''}")
    print(f"  mastered_ids({len(mastered)}个): {mastered[:10]}{'...' if len(mastered)>10 else ''}")
    print()
cur.close()
conn.close()
