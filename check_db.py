# check_db.py
import sqlite3

conn = sqlite3.connect('avito_learning.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print('Таблицы в базе:')
for table in tables:
    print(f'  - {table[0]}')
conn.close()