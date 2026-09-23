import psycopg2
from psycopg2 import sql
import hashlib
from time import sleep
from utils import *
import config
from youtube_api import get_one_video_stats, fetch_videos_stats, get_rss_feed, fetch_channel_id_from_video_id, get_video_tags
import requests as req
from datetime import datetime

def connection():
    conn = psycopg2.connect(
            dbname = "videal_algorithme",
            host = "localhost",
            port = 5432,
            user = "postgres",
            password = config.database_password
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

# def get_videos(username, limit, offset):
#     cur, conn = connection()
#     like_scale, view_scale, get_tag_settings, use_tag_settings = 1, 0.1, '', ''
#     if username :
#         cur.execute("""SELECT setting_like_scale, setting_view_scale, setting_tags_scale
#             FROM users
#             WHERE username = %s
#             ;""", [username])
#         like_scale, view_scale, tags_scale = cur.fetchone()
#         get_tag_settings = '''LEFT JOIN(
#                     SELECT videourl, COUNT(tcc.tags) AS nb_tags
#                     FROM has_tag ht 
#                     INNER JOIN (
#                             SELECT f.tags
#                             FROM follow_tags f
#                             JOIN users u ON u.user_pk = f.user_pk
#                             WHERE u.username = %s
#                     ) tcc ON ht.tags = tcc.tags
#                     GROUP BY videourl
#             ) tc ON tc.videourl = v.videourl'''
#         use_tag_settings = f'+ {tags_scale} * COALESCE(nb_tags, 0)'
#     request = f'''SELECT v.videourl,
#                COALESCE(u.username, 'UnknownFromYoutube') AS username,
#                COALESCE(lc.nb_likes, 0) + COALESCE(v.youtube_likes, 0)    AS nb_likes,
#                COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0)    AS nb_views,
#                COALESCE(u.channel_url, '')  AS channel_url,
#                COALESCE(lc.nb_dislikes, 0)  AS nb_dislikes,
#                v.is_hidden, 
#                v.is_youtube_video,
#                v.first_upload
#         FROM videos v
#         LEFT JOIN users u ON v.user_pk = u.user_pk 
#         LEFT JOIN (
#             SELECT videourl,
#                    COUNT(*) FILTER (WHERE NOT is_dislike) AS nb_likes,
#                    COUNT(*) FILTER (WHERE is_dislike)     AS nb_dislikes
#             FROM has_been_liked_by
#             GROUP BY videourl
#         ) lc ON lc.videourl = v.videourl
#         LEFT JOIN (
#             SELECT videourl, COUNT(*) AS nb_views
#             FROM has_been_viewed_by
#             GROUP BY videourl
#         ) vc ON vc.videourl = v.videourl
#         {get_tag_settings}
#         WHERE v.is_hidden = False
#         ORDER BY (
#             %s * CBRT( COALESCE(lc.nb_likes,0) + COALESCE(v.youtube_likes, 0) - COALESCE(lc.nb_dislikes,0) ) + %s * ( CBRT( COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0) )  ) {use_tag_settings}
#         ) DESC,
#         v.videourl ASC
#         LIMIT %s OFFSET %s
#         ;'''
#     if username:
#         cur.execute(request, [username, like_scale, view_scale, limit, offset])
#     else:
#         cur.execute(request, [like_scale, view_scale, limit, offset])
#     result = cur.fetchall()
#     close_connection(cur, conn)

#     return convert_sql_output_to_list_for_card(result)

def get_videos(username, limit, seen_video=[]):

    cur, conn = connection()

    like_scale, view_scale, get_tag_settings, use_tag_settings = 1, 0.1, '', ''
    score_expr = '''(
        %s * CBRT( COALESCE(lc.nb_likes,0) + COALESCE(v.youtube_likes, 0) - COALESCE(lc.nb_dislikes,0) )
        + %s * ( CBRT( COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0) ) )
        {use_tag_settings}
    )'''

    if username :
        cur.execute("""SELECT setting_like_scale, setting_view_scale, setting_tags_scale
            FROM users
            WHERE username = %s
            ;""", [username])
        like_scale, view_scale, tags_scale = cur.fetchone()
        get_tag_settings = '''LEFT JOIN(
                    SELECT videourl, COUNT(tcc.tags) AS nb_tags
                    FROM has_tag ht 
                    INNER JOIN (
                            SELECT f.tags
                            FROM follow_tags f
                            JOIN users u ON u.user_pk = f.user_pk
                            WHERE u.username = %s
                    ) tcc ON ht.tags = tcc.tags
                    GROUP BY videourl
            ) tc ON tc.videourl = v.videourl'''
        use_tag_settings = f'+ {tags_scale} * COALESCE(nb_tags, 0)'

        get_seen_settings = '''LEFT JOIN (
            SELECT DISTINCT hbvb.videourl
            FROM has_been_viewed_by hbvb
            JOIN users su ON su.user_pk = hbvb.user_pk
            WHERE su.username = %s
        ) sv ON sv.videourl = v.videourl'''
        seen_col = "COALESCE(sv.videourl, '') <> '' AS already_seen"

        score_for_row_number = score_expr.format(use_tag_settings=use_tag_settings)

    else:
        get_seen_settings = ''
        seen_col = 'False AS already_seen'

        score_for_row_number = score_expr.format(use_tag_settings='')

    request = f'''WITH ranked AS (
        SELECT v.videourl,
               COALESCE(u.username, 'UnknownFromYoutube') AS username,
               COALESCE(lc.nb_likes, 0) + COALESCE(v.youtube_likes, 0)    AS nb_likes,
               COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0)    AS nb_views,
               COALESCE(u.channel_url, '')  AS channel_url,
               COALESCE(lc.nb_dislikes, 0)  AS nb_dislikes,
               v.is_hidden, 
               v.is_youtube_video,
               v.first_upload,
               {score_for_row_number} AS score,
               {seen_col}
        FROM videos v
        LEFT JOIN users u ON v.user_pk = u.user_pk 
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
        {get_tag_settings}
        {get_seen_settings}
        WHERE v.is_hidden = False
    )
    SELECT videourl, username, nb_likes, nb_views, channel_url,
           nb_dislikes, is_hidden, is_youtube_video, first_upload,
           already_seen
    FROM ranked
    WHERE videourl != ALL(%s::text[])
    -- Tirage pondéré par le score (Gumbel) : les bonnes vidéos sortent
    -- plus souvent, mais chaque page est différente.
    ORDER BY -ln(-ln(random())) * GREATEST(score, 0.001) DESC,
             videourl ASC
    LIMIT %s
    ;'''

    if username:
        cur.execute(request, [like_scale, view_scale,
                              username,
                              username,
                              seen_video,
                              limit])
    else:
        cur.execute(request, [like_scale, view_scale,
                              seen_video,
                              limit])
    result = cur.fetchall()
    close_connection(cur, conn)

    return convert_sql_output_to_list_for_card(result)

def get_all_videos_from_channel(channel_usename, limit, offset, session_username=False):

    if session_username :
        get_seen_settings = '''LEFT JOIN (
            SELECT DISTINCT hbvb.videourl
            FROM has_been_viewed_by hbvb
            JOIN users su ON su.user_pk = hbvb.user_pk
            WHERE su.username = %s
        ) sv ON sv.videourl = v.videourl'''
        seen_col = "COALESCE(sv.videourl, '') <> '' AS already_seen"

    else:
        get_seen_settings = ''
        seen_col = 'False AS already_seen'

    cur, conn = connection()
    request = f'''
        SELECT v.videourl,
               u.username,
               COALESCE(lc.nb_likes, 0) + COALESCE(v.youtube_likes, 0)   AS nb_likes,
               COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0)   AS nb_views,
               u.channel_url               AS channel_url,
               COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
               v.is_hidden, 
               v.is_youtube_video,
               v.first_upload,
               {seen_col}
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
        {get_seen_settings}
        WHERE u.username = %s
        LIMIT %s OFFSET %s
        ;'''
    if session_username :
        cur.execute(request, [session_username, channel_usename, limit, offset])
    else:
        cur.execute(request, [channel_usename, limit, offset])

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

def add_video(video_id, username, first_upload_date = None):
    """
    first_upload_date prend un string format YYYY-MM-DD "2026-09-08"
    """
    user_pk = get_user_pk_from_username(username)
    if user_pk is None : raise ValueError("user 'One' not found")
    cur, conn = connection()
    if not first_upload_date:
        cur.execute("""INSERT INTO public.videos (videourl, user_pk)
                    VALUES (%s, %s)
                    ON CONFLICT (videourl) DO UPDATE
                    SET user_pk = EXCLUDED.user_pk
                ;""", [video_id, user_pk])
    else:
        cur.execute("""INSERT INTO public.videos (videourl, user_pk, first_upload)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (videourl) DO UPDATE
                            SET user_pk = EXCLUDED.user_pk
                        ;""", [video_id, user_pk, first_upload_date])
    close_connection(cur, conn)

def insert_new_youtube_video(video_id, first_upload_date = None):
    """
    first_upload_date prend un string format YYYY-MM-DD "2026-09-08"
    """
    try:
        cur, conn = connection()
        if not first_upload_date:
            cur.execute("""INSERT INTO public.videos (videourl,is_youtube_video)
                        VALUES (%s,true)
                        ;""", [video_id])
        else:
            cur.execute("""INSERT INTO public.videos (videourl,is_youtube_video, first_upload)
                                    VALUES (%s,true, %s)
                                    ;""", [video_id, first_upload_date])
        close_connection(cur, conn)
        return True
    except:
        return False

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

def get_video_data(video_id):
    cur, conn = connection()
    cur.execute("""SELECT   v.videourl,
                            COUNT(has_been_viewed_by) + COALESCE(v.youtube_views, 0) as nb_views,
                            v.first_upload,
                            v.is_youtube_video,
                            v.youtube_likes
                    FROM videos v
                    LEFT JOIN has_been_viewed_by ON v.videourl = has_been_viewed_by.videourl
                    WHERE v.videourl = %s
                    GROUP BY v.videourl;"""
        ,[video_id])
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result) == 0 : return False
    result = result[0]

    author_username, host_url = "", "youtube_url"
    if not result[3]: # If is not video youtube
        author_username, host_url, _ = get_author_info_from_video(video_id)

    first_upload_date = None
    if result[2]:
        first_upload_date = result[2].strftime("%d/%m/%Y")
    dict_result = {"videourl": result[0],
                   "nb_of_views": result[1],
                   "first_upload_date": first_upload_date,
                   "is_youtube_video": result[3],
                   "youtube_likes": result[4],
                   "author_username": author_username,
                   "host_url": host_url}
    return dict_result

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
                    COALESCE(lc.nb_likes, 0) + COALESCE(v.youtube_likes, 0)   AS nb_likes,
                    COALESCE(vc.nb_views, 0) + COALESCE(v.youtube_views, 0)   AS nb_views,
                    u.channel_url               AS channel_url,
                    COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
                    v.is_hidden, 
                    v.is_youtube_video,
                    v.first_upload,
                    COALESCE(sv.videourl, '') <> '' AS already_seen
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
                LEFT JOIN (
                    SELECT DISTINCT hbvb.videourl
                    FROM has_been_viewed_by hbvb
                    JOIN users su ON su.user_pk = hbvb.user_pk
                    WHERE su.username = %s
                ) sv ON sv.videourl = v.videourl
                JOIN is_following if ON v.user_pk = if.followed_pk
                WHERE if.follower_pk = %s
                LIMIT %s OFFSET %s
                ;""", [follower_username, follower_user_pk, limit, offset])
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

def update_user_setting(setting_name, value, username):
    try:
        cur, conn = connection()
        query = sql.SQL("""UPDATE users
                SET {col} = %s
                WHERE username = %s
                ;""").format(
            col=sql.Identifier(setting_name)
        )
        cur.execute(query, [value, username])
        close_connection(cur, conn)
        return True
    except:
        return False

def get_user_setting(username):
    cur, conn = connection()
    cur.execute("""SELECT setting_like_scale, setting_view_scale, setting_tags_scale
                FROM users
                WHERE username = %s
                ;""", [username])
    result = cur.fetchone()
    close_connection(cur, conn)
    return [setting for setting in result]

def get_user_followed_tags(username):
    cur, conn = connection()
    cur.execute("""SELECT tags
            FROM follow_tags f
            JOIN users u ON u.user_pk = f.user_pk
            WHERE u.username = %s
            ;""", [username])
    result = cur.fetchall()
    close_connection(cur, conn)
    return [tag[0] for tag in result]

def remove_followed_tag_from_user(tag_name, username):
    try:
        cur, conn = connection()
        cur.execute("""DELETE FROM follow_tags f
            USINg users u
            WHERE u.user_pk = f.user_pk AND u.username = %s AND f.tags = %s
            ;""", [username, tag_name])
        close_connection(cur, conn)
        return True
    except:
        return False

def add_tag_for_user_followed(tag_name, username):
    try:
        cur, conn = connection()
        cur.execute("""SELECT user_pk
            FROM users
            WHERE username = %s
        ;""", [username])
        user_pk = cur.fetchone()
        print(user_pk)
        if len(user_pk) == 0 : return False
        user_pk = user_pk[0]
        print(user_pk)
        cur.execute("""WITH new_tag AS (
                    INSERT INTO tags (tags)
                    VALUES (%s)
                    ON CONFLICT (tags) DO NOTHING
                    RETURNING tags
                )
                INSERT INTO follow_tags (user_pk, tags)
                SELECT %s, tags FROM new_tag
                UNION ALL
                SELECT %s, tags FROM tags WHERE tags = %s
                ;""", [tag_name, user_pk, user_pk, tag_name])
        close_connection(cur, conn)
        return True
    except:
        return False

def get_is_youtube_video(video_id):
    cur, conn = connection()
    cur.execute("""SELECT v.is_youtube_video
            FROM videos v
            WHERE v.videourl = %s
        ;""", [video_id])
    res = cur.fetchone()
    if res == None: raise ValueError(f"No video found with video_id={video_id}")
    close_connection(cur, conn)
    res = res[0]
    return res

def is_video_in_db(video_id):
    cur, conn = connection()
    cur.execute("""SELECT v.is_youtube_video
            FROM videos v
            WHERE v.videourl = %s
        ;""", [video_id])
    res = cur.fetchone()
    close_connection(cur, conn)
    return res != None

# do not spam:
def update_youtube_video_stats_with_api(video_id, force_api_key=None):
    if not get_is_youtube_video(video_id):
        raise ValueError(f"This video_id is not registered as a youtube video. video_id={video_id}")

    view_count, like_count = get_one_video_stats(video_id, force_api_key)

    if not view_count.isnumeric() or not like_count.isnumeric():
        raise ValueError(f"Error while accessing youtube stats. video_id={video_id}")

    cur, conn = connection()
    cur.execute("""UPDATE videos v
        SET youtube_views=%s , youtube_likes=%s, latest_stat_update=CURRENT_DATE
        WHERE v.videourl=%s
        ;""", [view_count, like_count, video_id])
    close_connection(cur, conn)

def get_all_youtube_videos():
    cur, conn = connection()
    cur.execute("""SELECT v.videourl 
        FROM videos v 
        WHERE v.is_youtube_video = TRUE;""")
    result = cur.fetchall()
    close_connection(cur, conn)
    if len(result) == 0 : return False
    result = [res[0] for res in result]
    return result

# do not spam:
def update_all_youtube_video_stats_with_api(force_api_key=None):
    videos_id_list = get_all_youtube_videos()

    videos_stats = fetch_videos_stats(videos_id_list, force_api_key)

    cur, conn = connection()
    for video_id in videos_stats:
        if not videos_stats[video_id]["view_count"].isnumeric() or not  videos_stats[video_id]["like_count"].isnumeric():
            print(f"Error while accessing youtube stats. video_id={video_id}")
            continue

        cur.execute("""UPDATE videos v
            SET youtube_views=%s , youtube_likes=%s
            WHERE v.videourl=%s
            ;""", [videos_stats[video_id]["view_count"], videos_stats[video_id]["like_count"], video_id])
    close_connection(cur, conn)
    return

# do not spam:
def update_youtube_videos_stats_from_list_with_api(list_of_video_id, force_api_key=None):

    videos_stats = fetch_videos_stats(list_of_video_id, force_api_key)

    cur, conn = connection()
    for video_id in videos_stats:
        if not videos_stats[video_id]["view_count"].isnumeric() or not  videos_stats[video_id]["like_count"].isnumeric():
            print(f"Error while accessing youtube stats. video_id={video_id}")
            continue

        cur.execute("""UPDATE videos v
            SET youtube_views=%s , youtube_likes=%s
            WHERE v.videourl=%s
            ;""", [videos_stats[video_id]["view_count"], videos_stats[video_id]["like_count"], video_id])
    close_connection(cur, conn)
    return

# do not spam:
def get_and_insert_all_video_from_youtube_channel(channel_id, force_api_key=None):
    """
    Request RSS feed, and for each video
    """

    list_of_video_data = get_rss_feed(channel_id)
    number_of_videos = len(list_of_video_data)
    number_of_successfully_inserted_videos = 0
    number_of_videos_already_in_db = 0

    # print("list_of_video_data :")
    # [print(vid) for vid in list_of_video_data]

    list_of_video_id_to_update = []

    for video_data in list_of_video_data:

        if is_video_in_db(video_data["video_id"]):
            number_of_videos_already_in_db +=1
            continue


        author_name = video_data["author_name"]
        author_url = video_data["author_url"]
        if not author_name or not author_url:
            continue

        list_of_video_id_to_update.append(video_data["video_id"])

        first_upload_date = video_data["first_upload_date"]
        try:
            date_obj = datetime.fromisoformat(first_upload_date)
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except:
            formatted_date = None
        insert_succesfull = insert_new_youtube_video(video_data["video_id"], formatted_date)
        if insert_succesfull :
            number_of_successfully_inserted_videos += 1
            if not youtuber_pfp_in_db(author_name, config.pfp_upload_folder):
                get_youtuber_pfp_from_video_id(author_name, author_url, config.pfp_upload_folder)
            fetch_and_add_video_tags(video_data["video_id"])

    # print("list_of_video_id_to_update :")
    # [print(vid) for vid in list_of_video_id_to_update]
    update_youtube_videos_stats_from_list_with_api(list_of_video_id_to_update, force_api_key)

    return f"{number_of_successfully_inserted_videos}/{number_of_videos} , {number_of_videos_already_in_db} videos already in database"

# do not spam
def schearch_and_insert_latest_videos_from_one_channel_from_video_id(video_id, force_api_key=None):
    channel_id = fetch_channel_id_from_video_id(video_id)
    if not channel_id:
        raise ValueError(f"This video_id does not return a channel_id. video_id={video_id}")
    print(get_and_insert_all_video_from_youtube_channel(channel_id, force_api_key))
    return 

def check_delay_between_video_update(video_id):
    cur, conn = connection()
    cur.execute("""SELECT latest_stat_update, CURRENT_DATE - latest_stat_update
                FROM videos
                WHERE videourl = %s
                ;""", [video_id])
    result = cur.fetchone()
    close_connection(cur, conn)
    if result is None : return result

    days_since_last_update = result[1]

    return config.DAYS_BETWEEN_CURRENT_DATE_AND_LATEST_STAT_UPDATE < days_since_last_update

# do not spam
def update_video_and_channel_with_delay_check(video_id):
    if check_delay_between_video_update(video_id):
        update_youtube_video_stats_with_api(video_id)
        schearch_and_insert_latest_videos_from_one_channel_from_video_id(video_id)

# do not spam
def fetch_and_add_video_tags(video_id):
    if not get_is_youtube_video(video_id):
        raise ValueError(f"This video is not registered as coming from Youtube. video_id={video_id}")
    
    tags_already_on_video = get_tags_of_video(video_id)
    nb_of_tags = len(tags_already_on_video)
    if nb_of_tags >= config.MAX_TAG_NUMBER_ON_VIDEO:
        print(f"This video already has {nb_of_tags} > config.MAX_TAG_NUMBER_ON_VIDEO = {config.MAX_TAG_NUMBER_ON_VIDEO}. video_id={video_id}")
        return
    
    tag_list = get_video_tags(video_id)[:max(config.MAX_TAG_NUMBER_ON_VIDEO-nb_of_tags,0)]
    # if len(tag_list) == 0: print("tag_list=[]")
    for tag in tag_list:
        if tag in tags_already_on_video: continue
        add_tag_on_video(video_id, tag)
        # print(video_id, tag)

def can_user_update_channel(username):
    cur, conn = connection()
    cur.execute("""SELECT can_update_channel
                FROM users
                WHERE username = %s
                ;""", [username])
    result = cur.fetchone()
    close_connection(cur, conn)
    if result is None : return result
    return result[0]

def can_user_add_youtube_video(username):
    cur, conn = connection()
    cur.execute("""SELECT can_add_youtube_video
                FROM users
                WHERE username = %s
                ;""", [username])
    result = cur.fetchone()
    close_connection(cur, conn)
    if result is None : return False
    return result[0]

if __name__ == "__main__" :
    print("Enter the database password : ")
    config.database_password = input()
    
    # print(get_comments_of_video("Bird"))
    # print(add_comment_on_video("Bird", "Leonardo", "It must fly so fast !"))
    # print(update_comment_from_pk(5, "It must fly so fast !!!"))
    # print(search_for_tag_request('anim'))
    # print(add_tag_on_video("Bird", "tag"))
    # print(get_followed_videos("One", 6, 0))
    # print(get_if_follow_channel('Walter White', 'Madeline'))
    # print(toggle_following_channel('Walter White', 'Madeline'))
    # print(get_list_of_followed_channels('One'))
    # print(update_user_setting("setting_like_scale", 10, "One"))
    # print(get_user_setting("One"))
    # print(get_user_followed_tags("One"))
    # print(remove_followed_tag_from_user('VLOG', 'One'))
    # print(add_tag_for_user_followed('pyhon', 'One'))
    # [print(vid) for vid in get_videos(False, 15, 0)]

    # print("Enter youtube API key :")
    # force_api_key = input()
    # # # update_youtube_video_stats_with_api("inujm9v5IT8", force_api_key)
    # # # print(get_all_youtube_videos())
    # # update_all_youtube_video_stats_with_api(force_api_key)
    # print(get_and_insert_all_video_from_youtube_channel("UCOKHwx1VCdgnxwbjyb9Iu1g", force_api_key))

    # print(can_user_update_channel("One"))
    # print(can_user_add_youtube_video("One"))

    # print(get_video_data("Bird"))
    # print(get_video_data("hnzMih9HWEE"))

    # print(check_delay_between_video_update("hnzMih9HWEE"))
    # fetch_and_add_video_tags("s28Y8ASchEk")
    # [fetch_and_add_video_tags(id) for id in get_all_youtube_videos()]
    