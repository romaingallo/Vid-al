import requests
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
import re
import os


def convert_sql_output_to_list_for_card(data_input):
    # Input  : [(url0, user_pk, nb_likes, nb_view), (url1, user_pk, nb_likes, nb_view)]
    # Output : [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    data_output = []
    for video_data in data_input:
        data_output.append({"channel": video_data[1], 
                            "views": str(video_data[3]), 
                            "likes": f"{video_data[2]}", 
                            "url": video_data[0], 
                            "hostURL":video_data[4], 
                            "is_hidden":video_data[6],
                            "is_youtube_video":video_data[7]})
    return data_output


def convert_sql_output_to_list_for_reactions(data_input):
    # Input  : [(is_dislike(False), nb_likes), (is_dislike(True), nb_dislikes), (is_dislike(None), nb_broken_likes)]
    # Output : [
    #     {"nb_likes": "12k", "nb_dislikes": "4k" }
    # ]
    data_output = {"likes" : data_input[0][1], "dislikes" : data_input[1][1]}
    return data_output

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def youtuber_pfp_in_db(author_name, pfp_folder):
    pfp_path_jpg = os.path.join(pfp_folder, f'{secure_filename(author_name)}.jpg')
    pfp_path_png = os.path.join(pfp_folder, f'{secure_filename(author_name)}.png')
    if os.path.exists(pfp_path_jpg) or os.path.exists(pfp_path_png): 
        return True
    return False

def get_youtuber_pfp_from_video_id(author_name, author_url, upload_folder):

    try:
        # Envoyer une requête GET pour récupérer l'image
        response = requests.get(author_url, stream=True)
        response.raise_for_status()  # Vérifier les erreurs HTTP

        soup = BeautifulSoup(response.text, "html.parser")
        # print(soup.prettify())
        # print(soup.find_all(string="yt3.googleusercontent.com"))

        pfp_url = None
        for script in soup.find_all('script'):
            if script.string and 'ytInitialData' in script.string:
                match = re.search(r'"avatar":\s*{\s*"thumbnails":\s*\[.*?"url":\s*"([^"]+)"', script.string)
                if match:
                    pfp_url = match.group(1)
                    break
        
        if pfp_url:
            # Change the size specification to get the small-size image
            pfp_url = re.sub(r'=s\d+-', '=s48-', pfp_url)
        else:
            print("No pfp_url found.")
            return False

        # print(pfp_url)
        
        reponse_image = requests.get(pfp_url, stream=True)
        reponse_image.raise_for_status()

        filename = secure_filename(author_name)
        filename = filename+ ".jpg"
        with open(os.path.join(upload_folder, filename), "wb") as fichier:
            for chunk in reponse_image.iter_content(1024):
                fichier.write(chunk)

        return True

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image : {e}")
        return False


if __name__ == '__main__':
    get_youtuber_pfp_from_video_id("RQWpF2Gb-gU", "3Blue1Brown", os.path.join(os.path.dirname(__file__), 'Interface client', 'images', 'profile_pictures'))