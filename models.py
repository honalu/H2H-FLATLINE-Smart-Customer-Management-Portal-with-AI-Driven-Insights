import sqlite3
def get_db():
    conn=sqlite3.connect('database.db')
    conn.row_factory=sqlite=sqlite3.Row
    return conn
def init_db():
    conn=get_db()
    conn.execute('''
                            CREATE TABLE IF NOT EXISTS customers(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            company_name TEXT,
                            region TEXT,
                            plan_tier TEXT,
                            nps_score INTEGER
                            )
                            ''')
    conn.commit()
    conn.close()

