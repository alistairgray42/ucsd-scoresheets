#!venv/bin/python

import sqlite3
import sys
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("INSERT INTO emails VALUES (?)", (sys.argv[1],))
