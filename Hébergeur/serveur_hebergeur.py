from flask import Flask, Response, send_file, jsonify
from flask_cors import CORS
import os
from utils import *
import json

app = Flask(__name__)
CORS(app)

current_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/video/<video_id>')
def stream_video(video_id):
    # Chemin vers le dossier des vidéos
    # video_dir = '/Vidéos'
    video_dir = os.path.join(current_dir, 'Vidéos')
    video_path = os.path.join(video_dir, f'{video_id}.mp4')
    
    # Vérifier si le fichier existe
    if not os.path.exists(video_path):
        return "Vidéo non trouvée", 404
        
    # Envoyer le fichier avec support du streaming
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        conditional=True  # Active le support des requêtes partielles
    )

@app.route('/meta/<video_id>')
def meta_video(video_id):
    # Chemin vers le dossier des vidéos
    # video_dir = '/meta'
    video_dir = os.path.join(current_dir, 'meta')
    meta_path = os.path.join(video_dir, f'{video_id}.json')
    
    # Vérifier si le fichier existe
    if not os.path.exists(meta_path):
        return "Metadata de la vidéo non trouvée", 404
        
    # Envoyer le fichier 
    return send_file(
        meta_path,
        mimetype='application/json',
        as_attachment=False
    )

@app.route('/channelinfo')
def channelinfo():

    meta_dir = os.path.join(current_dir, 'meta')
    videos_info = get_all_json(meta_dir)
    videos_info = json.dumps(videos_info)
    print(videos_info)
    if videos_info == []:
        return "No metadata found (json in meta file)", 404
    
    return Response(videos_info, mimetype='application/json')
    
    # return send_file(
    #     info_path,
    #     mimetype='application/json',
    #     as_attachment=False
    # )

@app.route('/thumbnail/<video_id>')
def thumbnail_video(video_id):
    # Chemin vers le dossier des vidéos
    # video_dir = '/thumbnail'
    video_dir = os.path.join(current_dir, 'thumbnail')
    thumbnail_path = os.path.join(video_dir, f'{video_id}.png')
    
    # Vérifier si le fichier existe
    if not os.path.exists(thumbnail_path):
        return "Miniature de la vidéo non trouvée", 404
        
    # Envoyer le fichier 
    return send_file(
        thumbnail_path,
        mimetype='image/png',
        as_attachment=False
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)