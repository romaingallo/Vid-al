from googleapiclient.discovery import build
import os
import feedparser
from utils import normalize_youtube_id

def get_one_video_stats(video_id, force_api_key=None):
    """
    Get view_count and like_count from video_id.  
    Ex : view_count, like_count = get_video_stats(video_id)
    """
    if force_api_key :
        api_key = force_api_key
    else:
        api_key = os.environ["API_KEY"]

    with build('youtube', 'v3', developerKey=api_key) as youtube:
        request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()

        # print(response)

        # Extraire les informations
        for video in response.get("items", []):
            stats = video.get("statistics", {})
            view_count = stats.get("viewCount", "N/A")
            like_count = stats.get("likeCount", "N/A")
            # print(f"Vues : {view_count}, Likes : {like_count}")
            return view_count, like_count

    return None, None


def get_videos_stats(video_ids, force_api_key=None):
    """
    Get view_count and like_count for a list of video_ids (50 vids max per api request).
    Returns a dictionary: {video_id: {"viewCount": ..., "likeCount": ...}}
    """
    if force_api_key:
        api_key = force_api_key
    else:
        api_key = os.environ["API_KEY"]

    results = {}

    nb_max_of_video = 50
    list_of_list = [video_ids[i:i + nb_max_of_video] for i in range(0, len(video_ids), nb_max_of_video)]

    for list_of_video_ids in list_of_list:

        with build('youtube', 'v3', developerKey=api_key) as youtube:
            # Joindre les IDs en une seule chaîne séparée par des virgules
            request = youtube.videos().list(
                part="statistics",
                id=','.join(list_of_video_ids)  # Ex: "video_id1,video_id2,video_id3"
            )
            response = request.execute()

            for video in response.get("items", []):
                stats = video.get("statistics", {})
                video_id = video.get("id")
                results[video_id] = {
                    "view_count": stats.get("viewCount", "N/A"),
                    "like_count": stats.get("likeCount", "N/A")
                }

    return results


def get_rss_feed(channel_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    feed = feedparser.parse(rss_url)

    videos_data = []
    for entry in feed.entries:
        # print(f"Titre: {entry.title}")
        # print(f"URL: {entry.link}")
        # print(f"Date de publication: {entry.published}")
        # print(f"Miniature: {entry.media_thumbnail[0]['url']}")
        video_id = entry.get('yt_videoid', {})
        # channel_id_entry = entry.get('yt_channelid', {})
        author_name = entry.get('author', {})
        author_url = entry.author_detail['href']
        # print(f"Video id: {video_id}")
        # print(f"channelId: {channel_id_entry}")
        # print(f"author name: {author_name}")
        # print(author_url)
        # print("---")
        data = {"video_id":normalize_youtube_id(entry.link),
                "author_name":author_name,
                "author_url":author_url,
                "first_upload_date":entry.get('published', None)}
        if not data["video_id"] or not data["author_name"] or not data["author_url"] : continue
        videos_data.append(data)
    return videos_data

if __name__ == "__main__" :
    [print(viddata) for viddata in get_rss_feed("UCROW1J2NQhg1Cd8y_XZ8e1g")]