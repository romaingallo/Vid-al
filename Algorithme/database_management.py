import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(
        dbname = "videal_algorithme",
        host = "localhost",
        port = 5432,
        user = "postgres",
        password = "0108"
        )

cur = conn.cursor()

conn.autocommit = True
# cur.execute("INSERT INTO users (username) VALUES (%s);",["Romain"])
# print(cur.fetchall())

cur.close()
conn.close()