from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from database_requests import *
import os

INTERFACE_DIR = os.path.join(os.path.dirname(__file__), 'Interface client')
app = Flask(__name__, static_folder=INTERFACE_DIR, static_url_path='')
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

@app.route('/')
def home():
    # path = os.path.join(os.path.dirname(__file__), '.', 'Interface client', 'main.html')
    # return send_file(os.path.abspath(path))
    return app.send_static_file('main.html')

@app.route('/api/videos')
def videos():
    # retourner une liste d'exemples; en pratique récupérer depuis DB
    data = convert_sql_output_to_json(get_all_videos())
    # data = [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    return jsonify(data)

@app.route('/api/channel/<channelId>')
def channel(channelId):
    # retourner une liste d'exemples; en pratique récupérer depuis DB
    data = convert_sql_output_to_json(get_all_videos_from_channel(channelId))
    # data = [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
