import psycopg2
from psycopg2 import sql

def connection():
    conn = psycopg2.connect(
            dbname = "videal_algorithme",
            host = "localhost",
            port = 5432,
            user = "postgres",
            password = "0108"
            )

    cur = conn.cursor()

    conn.autocommit = True

    return cur, conn

def close_connection(cur, conn):
    cur.close()
    conn.close()


def get_all_videos():
    cur, conn = connection()
    cur.execute("SELECT v.videourl, v.user_pk, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl)as nb_views from videos v LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl GROUP BY v.videourl;",[])
    result = cur.fetchall()
    close_connection(cur, conn)

    return result

if __name__ == "__main__" :
    print(get_all_videos())