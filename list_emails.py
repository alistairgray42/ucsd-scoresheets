#!venv/bin/python

import sqlite3
import sys
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM emails;")
for line in cursor:
    print(line[0])
conn.close()
