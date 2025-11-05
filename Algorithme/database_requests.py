import psycopg2
from psycopg2 import sql
import hashlib
from time import sleep

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
    cur.execute("SELECT v.videourl, u.username, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl)as nb_views from videos v JOIN users u ON v.user_pk = u.user_pk LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl GROUP BY v.videourl, u.username;",[])
    result = cur.fetchall()
    close_connection(cur, conn)

    return result

def get_all_videos_from_channel(channel_usename):
    cur, conn = connection()
    cur.execute("""SELECT 
                v.videourl, 
                u.username, 
                COUNT(DISTINCT l.videourl) as nb_likes, 
                COUNT(DISTINCT views.videourl) as nb_views 
            FROM videos v 
            JOIN users u ON v.user_pk = u.user_pk 
            LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl 
            LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl 
            WHERE u.username = %s
            GROUP BY v.videourl, u.username
            ;""",[channel_usename])
    result = cur.fetchall()
    close_connection(cur, conn)

    return result

def get_user_by_name(username):
    cur, conn = connection()
    cur.execute("""SELECT 
                username
            FROM users
            WHERE username = %s
            ;""",[username])
    result = cur.fetchall()
    close_connection(cur, conn)

    if len(result) > 0 : 
        for i in range(result) :
            result[i] = result[i][0]

    return result

def add_new_user(username, password):

    hashed_password = hashlib.sha256(password.encode('UTF-8')).hexdigest()

    cur, conn = connection()
    cur.execute("""INSERT INTO users 
                (username, password, register_date) 
                VALUES (%s, %s, current_date)
                ;""",
                [username, hashed_password])

    close_connection(cur, conn)

    return True

def authentification(username, password):

    sleep(0.05)

    hashed_password = hashlib.sha256(password.encode('UTF-8')).hexdigest()

    cur, conn = connection()
    cur.execute("""SELECT 
                username, password
                FROM users
                WHERE username = %s
                ;""",[username])
    result = cur.fetchall()
    close_connection(cur, conn)

    if len(result) > 0 :
        if hashed_password == result[0][1] : return True

    return False

if __name__ == "__main__" :
    print(get_all_videos())