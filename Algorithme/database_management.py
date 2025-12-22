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

like_scale = 1
limit = 12
offset = 12
cur.execute("SELECT v.videourl,"\
                "u.username, "\
                "COUNT(*) FILTER (WHERE not l.is_dislike) as nb_likes, "\
                "COUNT(DISTINCT views.videourl) as nb_views, "\
                "u.channel_url as channel_url, " \
                "COUNT(*) FILTER (WHERE l.is_dislike) as nb_dislikes, "\
                "(1 * CBRT( (COUNT(*) FILTER (WHERE not l.is_dislike) * 1.0) - (COUNT(*) FILTER (WHERE l.is_dislike) * 1.0) ) ) " \
        "FROM videos v " \
        "JOIN users u ON v.user_pk = u.user_pk " \
        "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
        "LEFT JOIN has_been_viewed_by views ON v.videourl = views.videourl " \
        "GROUP BY v.videourl, u.username, u.channel_url " \
        "ORDER BY ( " \
        "%s * CBRT( (COUNT(*) FILTER (WHERE not l.is_dislike) * 1.0) - (COUNT(*) FILTER (WHERE l.is_dislike) * 1.0) ) " \
        ") DESC " \
        "LIMIT %s OFFSET %s;"
        ,[like_scale, limit, offset])

# # Nb likes :
# cur.execute("SELECT v.videourl,"\
#         "COUNT(*) FILTER (WHERE not l.is_dislike) as nb_likes "\
#         "FROM videos v " \
#         "LEFT JOIN has_been_liked_by l ON v.videourl = l.videourl " \
#         "GROUP BY v.videourl;"
#         ,[])

# cur.execute("""SELECT id, titre, likes, dislikes, vues, commentaires, tags
# FROM videos
# WHERE [vos conditions de filtre, par exemple : tags LIKE '%musique%']
# ORDER BY (likes - dislikes) * log(vues + 1) DESC  -- Exemple de score personnalisé
# LIMIT 10 OFFSET 0;  -- Première page : 10 résultats
# """, ["video_id_aaaa", "7"])



print(cur.fetchall())

cur.close()
conn.close()