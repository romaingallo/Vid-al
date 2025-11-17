from flask import Flask, jsonify, request, send_file, redirect, url_for, session, render_template, flash
from flask_cors import CORS
from database_requests import *
import os
from datetime import timedelta
from werkzeug.utils import secure_filename

INTERFACE_DIR = os.path.join(os.path.dirname(__file__), 'Interface client')
app = Flask(__name__, static_folder=INTERFACE_DIR, static_url_path='', template_folder=INTERFACE_DIR)
app.secret_key = "secret_key"
app.permanent_session_lifetime = timedelta(minutes=5)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'Interface client', 'images', 'profile_pictures')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # max upload file size = 16 megabytes
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
    return render_template('main.html')

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
            return redirect(url_for('visit_channel', channel_name=session["user"]))
        return render_template('login.html')

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
        return render_template('register.html')

@app.route('/logout')
def logout():
    if "user" in session: session.pop("user", None)
    return redirect(url_for('home'))

@app.route('/api/videos')
def videos():
    data = get_all_videos()
    return jsonify(data)

@app.route('/api/channel/<channelId>')
def channel(channelId):
    data = get_all_videos_from_channel(channelId)
    return jsonify(data)

@app.route('/api/videos/<video_id>/react', methods=['POST'])
def react(video_id):
    data = request.get_json() or {}
    action = data.get('action')  # 'like', 'dislike', 'get' ...
    if action == 'get':
        result = get_reactions_on_video(video_id)
        if "user" in session: 
            result['personal_like_result'] = get_user_has_liked_for_json(video_id, session["user"])
        else :
            result['personal_like_result'] = 'no'

        return jsonify(result)
    if action == 'like' or action == 'dislike':
        if "user" in session:
            _, a = add_like_dislike(video_id, session["user"], action == 'dislike')

            result = get_reactions_on_video(video_id)
            result['personal_like_result'] = get_user_has_liked_for_json(video_id, session["user"])

            return jsonify(result)
    return jsonify({
        'likes': 'x',
        'dislikes': 'x',
        'personal_like_result': 'no',
        'user_reaction': None  # 'like' | 'dislike' | None
    })

@app.route('/pfp')
def pfp():
    if "user" in session:
        images_dir = os.path.join(current_dir, 'Interface client', 'images', 'profile_pictures')
        pfp_path = os.path.join(images_dir, f'{session["user"]}.png')

        minetype = 'image/png'

        # Vérifier si le fichier existe
        if not os.path.exists(pfp_path):
            minetype = 'image/svg+xml'
            images_dir = os.path.join(current_dir, 'Interface client', 'images') # Si on ne trouve pas de pfp
            pfp_path = os.path.join(images_dir, 'default_pfp.svg') # on revoie celle par défault
            if not os.path.exists(pfp_path):
                return "Profile picture not found", 404

        return send_file(
            pfp_path,
            mimetype=minetype,
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
    
@app.route('/pfp_of/<username>')
def pfp_of(username):
    images_dir = os.path.join(current_dir, 'Interface client', 'images', 'profile_pictures')
    pfp_path = os.path.join(images_dir, f'{username}.png')
    minetype = 'image/png'

    # Vérifier si le fichier existe
    if not os.path.exists(pfp_path):
        minetype = 'image/svg+xml'
        images_dir = os.path.join(current_dir, 'Interface client', 'images') # Si on ne trouve pas de pfp
        pfp_path = os.path.join(images_dir, 'default_pfp.svg') # on revoie celle par défault
        if not os.path.exists(pfp_path):
            return "Profile picture not found", 404
    
    return send_file(
        pfp_path,
        mimetype=minetype,
        as_attachment=False,
        conditional=True  # Active le support des requêtes partielles
    )
    
@app.route('/visit_channel/<channel_name>')
def visit_channel(channel_name):
    if "user" in session : 
        if session["user"] == channel_name :
            return render_template("visit_channel.html", name=channel_name, own_profile=True)
    return render_template("visit_channel.html", name=channel_name, own_profile=False)


@app.route('/watch/<video_id>')
def watch(video_id):
    reaction_result = get_reactions_on_video(video_id)
    green_state = 'green0'
    red_state   = 'red0'
    if "user" in session: 
        like_state = get_user_has_liked_for_json(video_id, session["user"])
        if like_state == 'like': green_state = 'green100'
        elif like_state == 'dislike' : red_state = 'red100'
    return render_template("watch.html", 
                           videoId=video_id, 
                           nb_likes=reaction_result["likes"], nb_dislikes=reaction_result["dislikes"], 
                           green_state=green_state, red_state=red_state)


@app.route('/upload_pfp', methods=['GET', 'POST'])
def upload_pfp():
    if "user" in session: 
        if request.method == 'POST':
            print(request.url)
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename, ['png']):
                # filename = secure_filename(file.filename)
                filename = f'{session["user"]}.png'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('home'))
            else :
                flash('The file should be a png.')
        return render_template("upload_pfp.html")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
