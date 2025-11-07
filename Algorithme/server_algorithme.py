from flask import Flask, jsonify, request, send_file, redirect, url_for, session
from flask_cors import CORS
from database_requests import *
import os
from datetime import timedelta

INTERFACE_DIR = os.path.join(os.path.dirname(__file__), 'Interface client')
app = Flask(__name__, static_folder=INTERFACE_DIR, static_url_path='')
app.secret_key = "secret_key"
app.permanent_session_lifetime = timedelta(minutes=5)
CORS(app)  # autorise toutes les origines (adapter en prod)

current_dir = os.path.dirname(os.path.abspath(__file__))

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
    if "user" in session:
        user = session["user"]
        print("user = " + user)
    else : print("not in session")
    return app.send_static_file('main.html')

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # print(request.form["usrname"] + " - " + request.form["psswrd"])
        if authentification(request.form["usrname"], request.form["psswrd"]) :
            session["user"] = request.form["usrname"]
            session.permanent = True
            return redirect(url_for('home'))
        else :
            return redirect(url_for('login', alert = "Invalid password or username."))
    else : 
        if "user" in session:
            print("sss")
            if "user" in session: session.pop("user", None)
            return redirect(url_for('home'))
        return app.send_static_file('login.html')

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username_input, password_input = request.form["usrname"], request.form["psswrd"]
        if len(username_input) < 1 or len(password_input) < 6 :
            return redirect(url_for('register', alert = "Invalid entry : the username should not be empty, and the password should be at least 6 characters."))
        elif len(get_user_by_name(username_input)) > 0 :
            return redirect(url_for('register', alert = "Username already taken."))
        else : # adding user + session
            add_new_user(username_input, password_input)
            print("new user created")
            return redirect(url_for('login', alert = "User created, you can now log in."))
            # session["user"] = request.form["usrname"]
            # session.permanent = True
        return redirect(url_for('register', alert = "An unknown error occurred."))
    else : 
        if "user" in session:
            redirect(url_for('home'))
        return app.send_static_file('register.html')

@app.route('/logout')
def logout():
    if "user" in session: session.pop("user", None)
    return redirect(url_for('home'))

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

@app.route('/pfp')
def pfp():
    if "user" in session:
        images_dir = os.path.join(current_dir, 'Interface client', 'images', 'profile_pictures')
        pfp_path = os.path.join(images_dir, 'Fur.png')

        # Vérifier si le fichier existe
        if not os.path.exists(pfp_path):
            return "Profile picture not found", 404
        
        return send_file(
            pfp_path,
            mimetype='image/png',
            as_attachment=False,
            conditional=True  # Active le support des requêtes partielles
        )
    else :
        images_dir = os.path.join(current_dir, 'Interface client', 'images')
        pfp_path = os.path.join(images_dir, 'user.svg')

        # Vérifier si le fichier existe
        if not os.path.exists(pfp_path):
            return "Profile picture not found", 404
        
        return send_file(
            pfp_path,
            mimetype='image/svg+xml',
            as_attachment=False,
            conditional=True  # Active le support des requêtes partielles
        )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
