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


# def get_all_videos():
#     cur, conn = connection()
#     cur.execute("SELECT v.videourl, u.username, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl) as nb_views, u.channel_url as channel_url " \
#     "FROM videos v " \
#     "JOIN users u ON v.user_pk = u.user_pk " \
#     "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
#     "LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl " \
#     "GROUP BY v.videourl, u.username, channel_url;",[])
#     result = cur.fetchall()
#     close_connection(cur, conn)

#     return convert_sql_output_to_list_for_card(result)

def get_videos(username, limit, offset):
    cur, conn = connection()
    like_scale, view_scale = 1, 0.1
    if username :
        cur.execute("""SELECT setting_like_scale, setting_view_scale
            FROM users
            WHERE username = %s
            ;""", [username])
        like_scale, view_scale = cur.fetchone()
    cur.execute("""
        SELECT v.videourl,
               u.username,
               COALESCE(lc.nb_likes, 0)    AS nb_likes,
               COALESCE(vc.nb_views, 0)    AS nb_views,
               u.channel_url               AS channel_url,
               COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
               v.is_hidden
        FROM videos v
        JOIN users u ON v.user_pk = u.user_pk
        LEFT JOIN (
            SELECT videourl,
                   COUNT(*) FILTER (WHERE NOT is_dislike) AS nb_likes,
                   COUNT(*) FILTER (WHERE is_dislike)     AS nb_dislikes
            FROM has_been_liked_by
            GROUP BY videourl
        ) lc ON lc.videourl = v.videourl
        LEFT JOIN (
            SELECT videourl, COUNT(*) AS nb_views
            FROM has_been_viewed_by
            GROUP BY videourl
        ) vc ON vc.videourl = v.videourl
        WHERE v.is_hidden = False
        ORDER BY (
            %s * CBRT( COALESCE(lc.nb_likes,0) - COALESCE(lc.nb_dislikes,0) ) + %s * CBRT( COALESCE(vc.nb_views, 0) )
        ) DESC
        LIMIT %s OFFSET %s
        ;""", [like_scale, view_scale, limit, offset])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_card(result)

def get_all_videos_from_channel(channel_usename, limit, offset):
    cur, conn = connection()
    cur.execute("""
        SELECT v.videourl,
               u.username,
               COALESCE(lc.nb_likes, 0)    AS nb_likes,
               COALESCE(vc.nb_views, 0)    AS nb_views,
               u.channel_url               AS channel_url,
               COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
               v.is_hidden
        FROM videos v
        JOIN users u ON v.user_pk = u.user_pk
        LEFT JOIN (
            SELECT videourl,
                   COUNT(*) FILTER (WHERE NOT is_dislike) AS nb_likes,
                   COUNT(*) FILTER (WHERE is_dislike)     AS nb_dislikes
            FROM has_been_liked_by
            GROUP BY videourl
        ) lc ON lc.videourl = v.videourl
        LEFT JOIN (
            SELECT videourl, COUNT(*) AS nb_views
            FROM has_been_viewed_by
            GROUP BY videourl
        ) vc ON vc.videourl = v.videourl
        WHERE u.username = %s
        LIMIT %s OFFSET %s
        ;""", [channel_usename, limit, offset])
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
    print(result)
    if len(result) > 0 : 
        for i in range(len(result)) :
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
    if len(result) == 0 : return False
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

def get_has_used_viewed(username, video_id): # Return True if the user has watched the video
    cur, conn = connection()
    cur.execute("""SELECT users.username
            FROM has_been_viewed_by
            LEFT JOIN users ON has_been_viewed_by.user_pk = users.user_pk
            WHERE users.username = %s AND has_been_viewed_by.videourl = %s
        ;""", [username, video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    return len(result)>0

def add_view(username, video_id):
    if get_has_used_viewed(username, video_id):
        return False, "Has already seen"
    user_pk = get_user_pk_from_username(username)
    if user_pk == False : return False, "Username not found"
    cur, conn = connection()
    cur.execute("""INSERT INTO has_been_viewed_by (videourl,user_pk)
        VALUES (%s,%s)
        ;""", [video_id,user_pk])
    close_connection(cur, conn)
    return True, "View added successfully"

def get_video_views(video_id):
    cur, conn = connection()
    cur.execute("SELECT v.videourl,"\
        "COUNT(has_been_viewed_by) as nb_views "\
        "FROM videos v " \
        "LEFT JOIN has_been_viewed_by ON v.videourl = has_been_viewed_by.videourl " \
        "WHERE v.videourl = %s " \
        "GROUP BY v.videourl;"
        ,[video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result) == 0 : return False
    return result[0][1]

def get_comments_of_video(video_id):
    cur, conn = connection()
    cur.execute("""SELECT u.username, c.content, c.date, c.comment_pk
                FROM comments c
                LEFT JOIN users u ON u.user_pk = c.user_pk
                WHERE c.videourl = %s
            ;""", [video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result) == 0 : return []
    return [list(tuple) for tuple in result]

def add_comment_on_video(video_id, username, comment_content):
    user_pk = get_user_pk_from_username(username)
    if user_pk == False : return False, "Username not found"
    cur, conn = connection()
    cur.execute("""INSERT INTO comments (videourl, user_pk, content)
            VALUES (%s, %s, %s)
            ;""", [video_id, user_pk, comment_content])
    close_connection(cur, conn)
    return True, "View added successfully"

def remove_comment_from_pk(comment_pk):
    try:
        cur, conn = connection()
        cur.execute("""DELETE FROM comments
            WHERE comment_pk = %s 
            ;""", [comment_pk])
        close_connection(cur, conn)
        return True
    except:
        return False
    
def update_comment_from_pk(comment_pk, comment_content):
    try:
        cur, conn = connection()
        cur.execute("""UPDATE comments
                SET content=%s
                WHERE comment_pk =%s
                ;""", [comment_content, comment_pk])
        close_connection(cur, conn)
        return True
    except:
        return False

def is_comment_from(comment_pk, username):
    cur, conn = connection()
    cur.execute("""SELECT u.username, c.content, c.date, c.comment_pk
            FROM comments c
            LEFT JOIN users u ON u.user_pk = c.user_pk
            WHERE c.comment_pk = %s AND u.username = %s
        ;""", [comment_pk, username])
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result) == 0 : return False
    return True

def get_param_of_video(video_id):
    cur, conn = connection()
    cur.execute("""SELECT v.is_hidden
            FROM videos v
            WHERE v.videourl = %s
        ;""", [video_id])
    is_hidden = cur.fetchone()
    cur.execute("""SELECT tags
                FROM has_tag
                WHERE videourl = %s
            ;""", [video_id])
    tags_list = cur.fetchall()
    close_connection(cur, conn)
    return [is_hidden[0], [tuple[0] for tuple in tags_list]]

def is_video_from(video_id, username):
    cur, conn = connection()
    cur.execute("""SELECT v.videourl
            FROM videos v
            LEFT JOIN users u ON u.user_pk = v.user_pk
            WHERE v.videourl = %s AND u.username = %s
        ;""", [video_id, username])
    result = cur.fetchone()
    close_connection(cur, conn)
    if result : return True
    return False

def toggle_is_hidden_of(video_id):
    try:
        cur, conn = connection()
        cur.execute("""UPDATE videos v
        SET is_hidden = NOT is_hidden
        WHERE v.videourl = %s
        ;""", [video_id])
        close_connection(cur, conn)
        return True
    except:
        return False

def get_tags_of_video(video_id):
    cur, conn = connection()
    cur.execute("""SELECT tags
                FROM has_tag
                WHERE videourl = %s
            ;""", [video_id])
    tags_list = cur.fetchall()
    close_connection(cur, conn)
    return [tuple[0] for tuple in tags_list]

def remove_tag_from_video(tag_name, video_id):
    try:
        cur, conn = connection()
        cur.execute("""DELETE FROM has_tag
            WHERE videourl = %s AND tags = %s
            ;""", [video_id, tag_name])
        close_connection(cur, conn)
        return True
    except:
        return False

def search_for_tag_request(tag_search):
    cur, conn = connection()
    cur.execute("""SELECT * 
            FROM tags t
            WHERE t.tags ILIKE %s
            LIMIT 7
            ;""", ['%'+tag_search+'%'])
    tags_list = cur.fetchall()
    close_connection(cur, conn)
    return [tuple[0] for tuple in tags_list]

def add_tag_on_video(video_id, tag):
    try:
        cur, conn = connection()
        cur.execute("""WITH new_tag AS (
                    INSERT INTO tags (tags)
                    VALUES (%s)
                    ON CONFLICT (tags) DO NOTHING
                    RETURNING tags
                )
                INSERT INTO has_tag (videourl, tags)
                SELECT %s, tags FROM new_tag
                UNION ALL
                SELECT %s, tags FROM tags WHERE tags = %s
                ;""", [tag, video_id, video_id, tag])
        close_connection(cur, conn)
        return True
    except:
        return False

def get_followed_videos(follower_username, limit, offset):
    follower_user_pk = get_user_pk_from_username(follower_username)
    if follower_user_pk == False : return []
    cur, conn = connection()
    cur.execute("""
                SELECT v.videourl,
                    u.username,
                    COALESCE(lc.nb_likes, 0)    AS nb_likes,
                    COALESCE(vc.nb_views, 0)    AS nb_views,
                    u.channel_url               AS channel_url,
                    COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
                    v.is_hidden
                FROM videos v
                JOIN users u ON v.user_pk = u.user_pk
                LEFT JOIN (
                    SELECT videourl,
                        COUNT(*) FILTER (WHERE NOT is_dislike) AS nb_likes,
                        COUNT(*) FILTER (WHERE is_dislike)     AS nb_dislikes
                    FROM has_been_liked_by
                    GROUP BY videourl
                ) lc ON lc.videourl = v.videourl
                LEFT JOIN (
                    SELECT videourl, COUNT(*) AS nb_views
                    FROM has_been_viewed_by
                    GROUP BY videourl
                ) vc ON vc.videourl = v.videourl
                JOIN is_following if ON v.user_pk = if.followed_pk
                WHERE if.follower_pk = %s
                LIMIT %s OFFSET %s
                ;""", [follower_user_pk, limit, offset])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_card(result)

def add_channel_to_follow(follower_username, channel_followed_username):
    try:
        cur, conn = connection()
        cur.execute("""INSERT INTO is_following (follower_pk, followed_pk)
                SELECT 
                    (SELECT user_pk FROM users WHERE username = %s), 
                    (SELECT user_pk FROM users WHERE username = %s)
                ;""", [follower_username, channel_followed_username])
        close_connection(cur, conn)
        return True
    except:
        return False

def remove_channel_to_follow(follower_username, channel_followed_username):
    try:
        cur, conn = connection()
        cur.execute("""DELETE FROM is_following
            WHERE follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
                    AND followed_pk = (SELECT user_pk FROM users WHERE username = %s)
            ;""", [follower_username, channel_followed_username])
        close_connection(cur, conn)
        return True
    except:
        return False

def get_if_follow_channel(follower_username, channel_followed_username):
    cur, conn = connection()
    cur.execute("""SELECT EXISTS(
                    SELECT 1
                    FROM is_following
                    WHERE follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
                            AND followed_pk = (SELECT user_pk FROM users WHERE username = %s)
                    )
            ;""", [follower_username, channel_followed_username])
    result = cur.fetchone()[0]
    close_connection(cur, conn)
    return result

def toggle_following_channel(follower_username, channel_followed_username):
    try:
        if get_if_follow_channel(follower_username, channel_followed_username):
            return remove_channel_to_follow(follower_username, channel_followed_username)
        return add_channel_to_follow(follower_username, channel_followed_username)
    except:
        return False

def get_list_of_followed_channels(follower_username):
    cur, conn = connection()
    cur.execute("""SELECT u.username 
            FROM users u 
            WHERE u.user_pk IN ( 
                SELECT if.followed_pk 
                FROM is_following if 
                WHERE if.follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
            )
            ;""", [follower_username])
    result = cur.fetchall()
    close_connection(cur, conn)
    return [tuple[0] for tuple in result]

if __name__ == "__main__" :
    # print(get_comments_of_video("Bird"))
    # print(add_comment_on_video("Bird", "Leonardo", "It must fly so fast !"))
    # print(update_comment_from_pk(5, "It must fly so fast !!!"))
    # print(search_for_tag_request('anim'))
    # print(add_tag_on_video("Bird", "tag"))
    # print(get_followed_videos("One", 6, 0))
    # print(get_if_follow_channel('Walter White', 'Madeline'))
    # print(toggle_following_channel('Walter White', 'Madeline'))
    print(get_list_of_followed_channels('One'))