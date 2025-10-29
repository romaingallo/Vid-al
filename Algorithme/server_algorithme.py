from flask import Flask, jsonify
from flask_cors import CORS
from database_requests import *

app = Flask(__name__)
CORS(app)  # autorise toutes les origines (adapter en prod)

def convert_sql_output_to_json(data_input):
    # Input  : [(url0, user_pk, nb_likes, nb_view), (url1, user_pk, nb_likes, nb_view)]
    # Output : [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    data_output = []
    for video_data in data_input:
        data_output.append({"channel": video_data[1], "views": str(video_data[3]), "likes": f"{video_data[2]}" , "url": video_data[0]})
    return data_output

@app.route('/api/videos')
def videos():
    # retourner une liste d'exemples; en pratique récupérer depuis DB
    data = convert_sql_output_to_json(get_all_videos())
    # data = [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
