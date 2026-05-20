"""
数据库重置脚本
用途：清空所有用户数据，重建 users 表
使用：python reset_db.py
"""

import psycopg2

DB_URL = (
    "postgresql://ranking_record_user:0DMQwPfdf8oIA0ttdtlUS6QkNqYU6Ure"
    "@dpg-d868ig9kh4rs73ck4ie0-a.oregon-postgres.render.com/ranking_record"
)

def reset():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS users;")
    print("✓ users 表已删除")

    cur.execute("""
        CREATE TABLE users (
            id                  SERIAL PRIMARY KEY,
            username            VARCHAR(50)  UNIQUE NOT NULL,
            password            VARCHAR(100) NOT NULL,
            location            VARCHAR(100) DEFAULT '',
            avatar_emoji        VARCHAR(10)  DEFAULT '🧑‍🎓',
            total_study_seconds INTEGER      DEFAULT 0,
            words_mastered      INTEGER      DEFAULT 0,
            words_learned       INTEGER      DEFAULT 0,
            streak_days         INTEGER      DEFAULT 0,
            last_study_date     VARCHAR(20)  DEFAULT '',
            learned_ids         TEXT         DEFAULT '[]',
            mastered_ids        TEXT         DEFAULT '[]',
            created_at          TIMESTAMPTZ  DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  DEFAULT NOW()
        );
    """)
    print("✓ users 表已重建（含最新结构）")

    cur.execute("SELECT COUNT(*) FROM users;")
    print(f"✓ 当前用户数：{cur.fetchone()[0]}")

    cur.close()
    conn.close()
    print("完成。")

if __name__ == "__main__":
    confirm = input("确认重置？所有用户数据将被清空。输入 yes 继续：")
    if confirm.strip().lower() == "yes":
        reset()
    else:
        print("已取消。")
