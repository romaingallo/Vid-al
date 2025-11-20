import psycopg2
from psycopg2 import sql
import hashlib
from time import sleep
from utils import *

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
    cur.execute("SELECT v.videourl, u.username, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl) as nb_views, u.channel_url as channel_url " \
    "FROM videos v " \
    "JOIN users u ON v.user_pk = u.user_pk " \
    "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
    "LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl " \
    "GROUP BY v.videourl, u.username, channel_url;",[])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_card(result)

def get_all_videos_from_channel(channel_usename):
    cur, conn = connection()
    cur.execute("""SELECT 
                v.videourl, 
                u.username, 
                COUNT(DISTINCT l.videourl) as nb_likes, 
                COUNT(DISTINCT views.videourl) as nb_views, 
                u.channel_url as channel_url 
            FROM videos v 
            JOIN users u ON v.user_pk = u.user_pk 
            LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl 
            LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl 
            WHERE u.username = %s
            GROUP BY v.videourl, u.username, channel_url
            ;""",[channel_usename])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_card(result)

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

def get_reactions_on_video(video_id):
    cur, conn = connection()
    cur.execute("""WITH agg AS (
                SELECT is_dislike, COUNT(*) AS nb
                FROM has_been_liked_by
                WHERE videourl = %s
                GROUP BY is_dislike
            )
            SELECT v.is_dislike, COALESCE(agg.nb, 0) AS nb
            FROM (VALUES (false), (true), (NULL::boolean)) AS v(is_dislike)
            LEFT JOIN agg ON (agg.is_dislike IS NOT DISTINCT FROM v.is_dislike)
            ORDER BY v.is_dislike
            ;""",[video_id])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_reactions(result)

def get_user_pk_from_username(username):
    cur, conn = connection()
    cur.execute("""SELECT user_pk
            FROM users
            WHERE username = %s
        ;""", [username])
    result = cur.fetchall()
    close_connection(cur, conn)

    return result[0][0]

def update_like(video_id, username, is_dislike):
    cur, conn = connection()
    cur.execute("""UPDATE has_been_liked_by hblb
        SET is_dislike=%s
        WHERE hblb.videourl=%s
        AND hblb.user_pk = (SELECT user_pk FROM users WHERE username=%s)
        ;""", [is_dislike, video_id, username])
    close_connection(cur, conn)

def delete_like(video_id, username):
    try:
        cur, conn = connection()
        cur.execute("""DELETE FROM has_been_liked_by hblb
            WHERE videourl= %s 
            AND hblb.user_pk = (SELECT user_pk FROM users WHERE username=%s)
            ;""", [video_id, username])
        close_connection(cur, conn)
        return True
    except:
        return False

def add_like_dislike(video_id, username, is_dislike): # Return ok (bool)
    has_already_liked, already_is_dislike = get_user_has_liked(video_id, username)
    if has_already_liked and already_is_dislike == is_dislike : 
        return delete_like(video_id, username), "Has already liked/disliked, tried removing it"
    elif has_already_liked and already_is_dislike != is_dislike : 
        update_like(video_id, username, is_dislike)
        return True, "Has already liked/disliked, but has been updated"

    user_pk = get_user_pk_from_username(username) # Otpimisable : faire une seule requete sql
    cur, conn = connection()
    is_dislike_request = "false"
    if is_dislike : is_dislike_request = "true"
    cur.execute("""INSERT INTO has_been_liked_by (videourl,user_pk,is_dislike)
	VALUES (%s,%s,%s)
        ;""", [video_id,user_pk,is_dislike_request])
    close_connection(cur, conn)
    return True, "Like/Dislike added successfully"

def get_user_has_liked(video_id, username): # Return (True, is_dislike) if the user has liked or disliked the video
    cur, conn = connection()
    cur.execute("""SELECT is_dislike
            FROM has_been_liked_by
            LEFT JOIN users ON has_been_liked_by.user_pk = users.user_pk
            WHERE users.username = %s AND has_been_liked_by.videourl = %s
        ;""", [username, video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result)<1 : return (False, False)
    else:
        return (True, result[0][0])

def get_user_has_liked_for_json(video_id, username):
    has_already_liked, already_is_dislike = get_user_has_liked(video_id, username)
    if has_already_liked : 
        if already_is_dislike :
            return 'dislike'
        else :
            return 'like'
    else :
        return 'no'

def update_channel_url(url, username):
    cur, conn = connection()
    cur.execute("""UPDATE public.users
	SET channel_url=%s
	WHERE username=%s
        ;""", [url, username])
    close_connection(cur, conn)

def add_video(video_id, username):
    user_pk = get_user_pk_from_username(username)
    if user_pk is None : raise ValueError("user 'One' not found")
    cur, conn = connection()
    cur.execute("""INSERT INTO public.videos (videourl, user_pk)
                VALUES (%s, %s)
                ON CONFLICT (videourl) DO UPDATE
                SET user_pk = EXCLUDED.user_pk
            ;""", [video_id, user_pk])
    close_connection(cur, conn)

def get_author_info_from_video(video_id):
    cur, conn = connection()
    cur.execute("""SELECT username, channel_url, register_date
            FROM users
            LEFT JOIN videos ON videos.user_pk = users.user_pk
            WHERE videos.videourl = %s
        ;""", [video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    return result[0]

def get_host_url_from_username(username):
    cur, conn = connection()
    cur.execute("""SELECT channel_url
            FROM users
            WHERE username = %s
        ;""", [username])
    result = cur.fetchall()
    close_connection(cur, conn)
    return result[0]

if __name__ == "__main__" :
    print(get_host_url_from_username("Quentin"))