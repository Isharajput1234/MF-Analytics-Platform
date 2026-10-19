
from pathlib import Path
import sqlite3

db_path = Path("db/bluestock_mf.db")
sql_path = Path("sql/queries.sql")

sql_text = sql_path.read_text(encoding="utf-8")
queries = [
    q.strip()
    for q in sql_text.split(";")
    if q.strip()
]

with sqlite3.connect(db_path) as conn:
    for i, query in enumerate(queries, start=1):
        print(f"\n{'=' * 15} QUERY {i} {'=' * 15}")
        try:
            cursor = conn.execute(query)
            columns = [col[0] for col in cursor.description]
            print(columns)
            for row in cursor.fetchmany(10):
                print(row)
        except sqlite3.Error as error:
            print("SQL Error:", error)
