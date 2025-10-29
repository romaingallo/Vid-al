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
cur.execute("SELECT v.videourl, v.user_pk, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl)as nb_views from videos v LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl GROUP BY v.videourl;",[])
print(cur.fetchall())

cur.close()
conn.close()