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
# cur.execute("INSERT INTO users (username, password, register_date) VALUES (%s, %s, current_date);",["Romain", "mdp"])
# cur.execute("SELECT v.videourl, u.username, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl)as nb_views from videos v JOIN users u ON v.user_pk = u.user_pk LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl GROUP BY v.videourl, u.username;",[])
# cur.execute("SELECT v.videourl, u.username FROM videos v JOIN users u ON v.user_pk = u.user_pk;",[])
# cur.execute("""SELECT 
#                 v.videourl, 
#                 u.username, 
#                 COUNT(DISTINCT l.videourl) as nb_likes, 
#                 COUNT(DISTINCT views.videourl) as nb_views 
#             FROM videos v 
#             JOIN users u ON v.user_pk = u.user_pk 
#             LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl 
#             LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl 
#             WHERE u.username = %s
#             GROUP BY v.videourl, u.username
#             ;""",['Romain'])
# cur.execute("""SELECT 
#                 username
#             FROM users
#             WHERE username = %s
#             ;""",['Romai'])
# cur.execute("""SELECT 
#                 username, password
#             FROM users
#             WHERE username = %s
#             ;""",['One'])
# cur.execute("""WITH agg AS (
#                 SELECT is_dislike, COUNT(*) AS nb
#                 FROM has_been_liked_by
#                 WHERE videourl = %s
#                 GROUP BY is_dislike
#             )
#             SELECT v.is_dislike, COALESCE(agg.nb, 0) AS nb
#             FROM (VALUES (false), (true), (NULL::boolean)) AS v(is_dislike)
#             LEFT JOIN agg ON (agg.is_dislike IS NOT DISTINCT FROM v.is_dislike)
#             ORDER BY v.is_dislike
#             ;""",['video_test_01'])
# cur.execute("""INSERT INTO has_been_liked_by (videourl,user_pk,is_dislike)
# 	VALUES (%s,%s,%s)
#         ;""", ['video_test_00','1','false'])
# cur.execute("""SELECT user_pk
#             FROM users
#             WHERE username = %s
#         ;""", ['Romain'])
# cur.execute("""SELECT is_dislike
#             FROM has_been_liked_by
#             LEFT JOIN users ON has_been_liked_by.user_pk = users.user_pk
#             WHERE users.username = %s AND has_been_liked_by.videourl = %s
#         ;""", ['Romain', 'video_test_01'])

# cur.execute("""UPDATE has_been_liked_by hblb
#         SET is_dislike=%s
#         WHERE hblb.videourl=%s
#         AND hblb.user_pk = (SELECT user_pk FROM users WHERE username=%s)
#         ;""", ['true', 'video_test_01', 'Romain'])

# cur.execute("""DELETE FROM has_been_liked_by hblb
# 	WHERE videourl= %s 
# 	AND hblb.user_pk = (SELECT user_pk FROM users WHERE username=%s)
# 	;""", ['video_test_00', 'One'])

# cur.execute("""UPDATE public.users
# 	SET channel_url=%s
# 	WHERE username=%s
#         ;""", ['url', 'One'])

# cur.execute("""INSERT INTO public.videos (videourl,user_pk)
# 	            VALUES (%s,(SELECT user_pk FROM users WHERE username=%s));
#                 """, ["video_id_aaaa", "One"])
# cur.execute("""INSERT INTO public.videos (videourl, user_pk)
#                 VALUES (%s, %s)
#                 ON CONFLICT (videourl) DO UPDATE
#                 SET user_pk = EXCLUDED.user_pk
#             ;""", ["video_id_aaaa", "7"])

# cur.execute("""SELECT username, channel_url, register_date
#             FROM users
#             LEFT JOIN videos ON videos.user_pk = users.user_pk
#             WHERE videos.videourl = %s
#         ;""", ['video_test_00'])

# Get all videos :
# SELECT v.videourl, u.username, COUNT(DISTINCT l.videourl) as nb_likes, COUNT(DISTINCT views.videourl) as nb_views, u.channel_url as channel_url " \
#     "FROM videos v " \
#     "JOIN users u ON v.user_pk = u.user_pk " \
#     "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
#     "LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl " \
#     "GROUP BY v.videourl, u.username, channel_url;

# # # Get videos :
# like_scale = 1
# limit = 12
# offset = 0
# view_scale = 0.1
# cur.execute("""
#         SELECT v.videourl,
#                u.username,
#                COALESCE(lc.nb_likes, 0)    AS nb_likes,
#                COALESCE(vc.nb_views, 0)    AS nb_views,
#                u.channel_url               AS channel_url,
#                COALESCE(lc.nb_dislikes, 0) AS nb_dislikes
#         FROM videos v
#         JOIN users u ON v.user_pk = u.user_pk
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
#         ORDER BY (
#             %s * CBRT( COALESCE(lc.nb_likes,0) - COALESCE(lc.nb_dislikes,0) ) + %s * CBRT( COALESCE(vc.nb_views, 0) )
#         ) DESC
#         LIMIT %s OFFSET %s
#         ;""", [like_scale, view_scale, limit, offset])

# # Nb likes :
# cur.execute("SELECT v.videourl,"\
#         "COUNT(*) FILTER (WHERE not l.is_dislike) as nb_likes "\
#         "FROM videos v " \
#         "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
#         "GROUP BY v.videourl;"
#         ,[])


# # Get get_user_has_view(user, video_id) :
# cur.execute("""SELECT users.username
#             FROM has_been_viewed_by
#             LEFT JOIN users ON has_been_viewed_by.user_pk = users.user_pk
#             WHERE users.username = %s AND has_been_viewed_by.videourl = %s
#         ;""", ['Romain', 'video_test_01'])

# # Add a view
# cur.execute("""INSERT INTO has_been_viewed_by (videourl,user_pk)
# 	VALUES (%s,%s)
#         ;""", ["Bird",10])

# Number of views :
# cur.execute("SELECT v.videourl,"\
#         "COUNT(has_been_viewed_by) as nb_views "\
#         "FROM videos v " \
#         "LEFT JOIN has_been_viewed_by ON v.videourl = has_been_viewed_by.videourl " \
#         "GROUP BY v.videourl;"
#         ,[])
# cur.execute("SELECT v.videourl,"\
#         "COUNT(has_been_viewed_by) as nb_views "\
#         "FROM videos v " \
#         "LEFT JOIN has_been_viewed_by ON v.videourl = has_been_viewed_by.videourl " \
#         "WHERE v.videourl = %s " \
#         "GROUP BY v.videourl;"
#         ,['video_test_01'])


# res = cur.fetchall()
# for i in res:
#         print(i)

# # Commentaires :
# get
# cur.execute("""SELECT u.username, c.content, c.date, c.comment_pk
#             FROM comments c
#             LEFT JOIN users u ON u.user_pk = c.user_pk
#             WHERE c.videourl = %s
#         ;""", ['Bird'])
# add
# cur.execute("""INSERT INTO comments (videourl, user_pk, content)
#         VALUES (%s, %s, %s)
#         ;""", ["Bird", 1, "Nice video"])
# remove
# cur.execute("""DELETE FROM comments
# 	WHERE comment_pk = %s 
# 	;""", [3])
# edit
# cur.execute("""UPDATE comments
#         SET content=%s
#         WHERE comment_pk =%s
#         ;""", ['AMazing video', 2])
# get if username
# cur.execute("""SELECT u.username, c.content, c.date, c.comment_pk
#             FROM comments c
#             LEFT JOIN users u ON u.user_pk = c.user_pk
#             WHERE c.comment_pk = %s AND u.username = %s
#         ;""", [6, 'One'])



# test auteur de video
# cur.execute("""SELECT v.videourl
#             FROM videos v
#             LEFT JOIN users u ON u.user_pk = v.user_pk
#             WHERE v.videourl = %s AND u.username = %s
#         ;""", ['Howls_piano', 'One'])



# Edit video
# get parameters
# cur.execute("""SELECT v.is_hidden
#             FROM videos v
#             WHERE v.videourl = %s
#         ;""", ['Howls_piano'])
# toggle is_hidden
# cur.execute("""UPDATE videos v
#         SET is_hidden = NOT is_hidden
#         WHERE v.videourl = %s
#         ;""", ['Howls_piano'])

# Tags
# get from video
# cur.execute("""SELECT tags
#             FROM has_tag
#             WHERE videourl = %s
#         ;""", ['Howls_piano'])
# create tag (new tag)
# cur.execute("""INSERT INTO tags (tags)
#         VALUES (%s)
#         ;""", ["Gaming"])
# add tag to video
# cur.execute("""INSERT INTO has_tag (videourl, tags)
#         VALUES (%s, %s)
#         ;""", ['video_test_00', 'Humour'])
# remove tag from video
# cur.execute("""DELETE FROM has_tag
# 	WHERE videourl = %s AND tags = %s
# 	;""", ['video_test_00', 'Gaming'])
# search for tag
# cur.execute("""SELECT * 
#             FROM tags
#             WHERE to_tsvector('french', tags) @@ to_tsquery('french', %s)
#             LIMIT 7
#             ;""", ['anim'])
# cur.execute("""SELECT * 
#             FROM tags t
#             WHERE t.tags ILIKE %s
#             LIMIT 7
#             ;""", ['%an%'])
# add and create tag to video if no tag
# video_id, tag_name = 'video_test_00', 'VLOG'
# cur.execute("""WITH new_tag AS (
#                 INSERT INTO tags (tags)
#                 VALUES (%s)
#                 ON CONFLICT (tags) DO NOTHING
#                 RETURNING tags
#             )
#             INSERT INTO has_tag (videourl, tags)
#             SELECT %s, tags FROM new_tag
#             UNION ALL
#             SELECT %s, tags FROM tags WHERE tags = %s
#             ;""", [tag_name, video_id, video_id, tag_name])


# # get followed video
# follower_user_pk, limit, offset = 7, 8, 0
# cur.execute("""
#         SELECT v.videourl,
#                u.username,
#                COALESCE(lc.nb_likes, 0)    AS nb_likes,
#                COALESCE(vc.nb_views, 0)    AS nb_views,
#                u.channel_url               AS channel_url,
#                COALESCE(lc.nb_dislikes, 0) AS nb_dislikes,
#                v.is_hidden
#         FROM videos v
#         JOIN users u ON v.user_pk = u.user_pk
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
#         JOIN is_following if ON v.user_pk = if.followed_pk
#         WHERE if.follower_pk = %s
#         LIMIT %s OFFSET %s
#         ;""", [follower_user_pk, limit, offset])

# add a channel to follow
# cur.execute("""INSERT INTO is_following (follower_pk, followed_pk)
#         SELECT 
#             (SELECT user_pk FROM users WHERE username = %s), 
#             (SELECT user_pk FROM users WHERE username = %s)
#         ;""", ['Walter White', 'Madeline'])
# remove a channel to follow
# cur.execute("""DELETE FROM is_following
# 	WHERE follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
#             AND followed_pk = (SELECT user_pk FROM users WHERE username = %s)
# 	;""", ['Walter White', 'Madeline'])
# get if follow channel
# cur.execute("""SELECT EXISTS(
#                 SELECT 1
#                 FROM is_following
#                 WHERE follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
#                         AND followed_pk = (SELECT user_pk FROM users WHERE username = %s)
#                 )
#         ;""", ['Walter White', 'Madeline'])
# get list of followed channels
# cur.execute("""SELECT u.username 
#             FROM users u 
#             WHERE u.user_pk IN ( 
#                 SELECT if.followed_pk 
#                 FROM is_following if 
#                 WHERE if.follower_pk = (SELECT user_pk FROM users WHERE username = %s) 
#             )
#             ;""", ['One'])

# Get settings for algo
cur.execute("""SELECT setting_like_scale, setting_view_scale
            FROM users
            WHERE username = %s
            ;""", ['One'])


# print(cur.fetchall())
print(cur.fetchone())

cur.close()
conn.close()