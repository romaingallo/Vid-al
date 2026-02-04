from flask import Flask, jsonify, request, send_file, redirect, url_for, session, render_template, flash
from flask_cors import CORS
from database_requests import *
import os
from datetime import timedelta
from werkzeug.utils import secure_filename
import requests as req
import json

INTERFACE_DIR = os.path.join(os.path.dirname(__file__), 'Interface client')
app = Flask(__name__, static_folder=INTERFACE_DIR, static_url_path='', template_folder=INTERFACE_DIR)
app.secret_key = "secret_key"
app.permanent_session_lifetime = timedelta(minutes=5)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'Interface client', 'images', 'profile_pictures')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # max upload file size = 16 megabytes
CORS(app)  # autorise toutes les origines (adapter en prod)

MAX_TAG_NUMBER_ON_VIDEO = 5
NUMBER_OF_VIDEO_PER_FETCH = 6 # -> le fecth javascript fait des offsets de 6, n'est pas lié à cette variable

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
    return render_template('html/main.html',
                           connected = "user" in session)

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        if authentification(request.form["usrname"], request.form["psswrd"]) :
            session["user"] = request.form["usrname"]
            session.permanent = True
            return redirect(url_for('home'))
        else :
            flash("Invalid password or username.")
            return redirect(url_for('login'))
    else : 
        if "user" in session:
            return redirect(url_for('visit_channel', channel_name=session["user"]))
        return render_template('html/login.html',
                               connected = "user" in session)

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username_input, password_input = request.form["usrname"], request.form["psswrd"]
        if len(username_input) < 1 or len(password_input) < 6 :
            flash("Invalid entry : the username should not be empty, and the password should be at least 6 characters.")
            return redirect(url_for('register'))
        elif len(get_user_by_name(username_input)) > 0 :
            flash("Username already taken.")
            return redirect(url_for('register'))
        else : # adding user + session
            add_new_user(username_input, password_input)
            flash("User created, you can now log in.")
            return redirect(url_for('login'))
            # session["user"] = request.form["usrname"]
            # session.permanent = True
        return redirect(url_for('register', alert = "An unknown error occurred."))
    else : 
        if "user" in session:
            redirect(url_for('home'))
        return render_template('html/register.html',
                               connected = "user" in session)

@app.route('/logout')
def logout():
    if "user" in session: session.pop("user", None)
    return redirect(url_for('home'))

@app.route('/api/videos/<offset>')
def videos(offset):
    like_scale = 1
    NUMBER_OF_VIDEO_PER_FETCH = 6
    view_scale = 0.1
    data = get_videos(like_scale, view_scale, NUMBER_OF_VIDEO_PER_FETCH, offset)
    return jsonify(data)

@app.route('/api/channel/<channelId>/<offset>')
def channel(channelId, offset):
    NUMBER_OF_VIDEO_PER_FETCH = 6
    data = get_all_videos_from_channel(channelId, NUMBER_OF_VIDEO_PER_FETCH, offset)
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

@app.route('/api/deletecomment', methods=['POST'])
def deletecomment():
    if request.method == 'POST':
        if "user" in session: 
            comment_id = request.form.get('comment_id')
            if is_comment_from(comment_id, session["user"]):
                remove_comment_from_pk(comment_id)
                return '', 200
            return jsonify({"error": 'User Unauthorized'}), 401
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

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
    host_url = get_host_url_from_username(channel_name)
    if "user" in session : 
        return render_template("html/visit_channel.html", 
                                   name=channel_name, 
                                   own_profile= session["user"] == channel_name, 
                                   hostURL=host_url,
                                   connected = "user" in session,
                                   is_following = get_if_follow_channel(session["user"], channel_name))
    return render_template("html/visit_channel.html", 
                           name=channel_name, 
                           own_profile=False, 
                           hostURL=host_url,
                           connected = "user" in session)

@app.route('/api/followedvideos/<offset>')
def followedvideos(offset):
    if "user" in session : 
        NUMBER_OF_VIDEO_PER_FETCH = 6
        data = get_followed_videos(session["user"], NUMBER_OF_VIDEO_PER_FETCH, offset)
        return jsonify(data), 200
    return jsonify({"error": 'User Unauthorized'}), 401

@app.route('/api/togglefollowing', methods=['POST'])
def togglefollowing():
    if request.method == 'POST':
        if "user" in session : 
            channel_followed_username = request.form.get('channel_followed_username')
            if not channel_followed_username : jsonify({"error": "channel_followed_username is missing."}), 400
            if toggle_following_channel(session["user"], channel_followed_username):
                return '', 200
            return jsonify({"error": 'Toggling the follow failed.'}), 500
        return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

@app.route('/followed')
def followed():
    return render_template("html/followed.html",
                           connected = "user" in session)

@app.route('/userfollowedlist')
def userfollowedlist():
    if "user" in session :
        return render_template("html/userfollowedlist.html",
                            list_of_followed_channels = get_list_of_followed_channels(session["user"]))
    return 'User not in session : no followed list.', 401

@app.route('/edit/<channel_name>/<video_id>')
def edit(channel_name, video_id):
    parameters = get_param_of_video(video_id)
    return render_template("html/edit_video.html",
                           is_hidden = parameters[0],
                           channel_name = channel_name,
                           video_id = video_id,
                           tag_list = parameters[1],
                           connected = "user" in session)

@app.route('/api/edit/toggle_is_hidden', methods=['POST'])
def toggle_is_hidden():
    if request.method == 'POST':
        if "user" in session: 
            video_id = request.form.get('video_id')
            if is_video_from(video_id, session["user"]):
                if toggle_is_hidden_of(video_id):
                    return '', 200
                else : return jsonify({"error": 'Toggle failed'}), 500
            else: return jsonify({"error": 'User Unauthorized'}), 401
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

@app.route('/api/edit/remove_tag', methods=['POST'])
def remove_tag():
    if request.method == 'POST':
        if "user" in session: 
            video_id = request.form.get('video_id')
            if is_video_from(video_id, session["user"]):
                tag_name = request.form.get('tag_name')
                if remove_tag_from_video(tag_name, video_id):
                    return '', 200
                else : return jsonify({"error": f'Internal error when deletion of tag {tag_name}'}), 500
            else: return jsonify({"error": 'User Unauthorized'}), 401
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

@app.route('/api/edit/add_tag', methods=['POST'])
def add_tag():
    if request.method == 'POST':
        if "user" in session: 
            video_id = request.form.get('video_id')
            if is_video_from(video_id, session["user"]):
                list_tags_on_video = get_tags_of_video(video_id)
                if len(list_tags_on_video)+1 > MAX_TAG_NUMBER_ON_VIDEO: return jsonify({"error": f'The video has already been tagged {MAX_TAG_NUMBER_ON_VIDEO} times (max per video).'}), 500
                tag_name = request.form.get('tag_name')
                if tag_name in list_tags_on_video: return jsonify({"error": f'The video has already been tagged {tag_name}.'}), 500
                if add_tag_on_video(video_id, tag_name):
                    return '', 200
                else : return jsonify({"error": f'Internal error when adding tag {tag_name}'}), 500
            else: return jsonify({"error": 'User Unauthorized'}), 401
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

@app.route('/api/search/tag', methods=['POST'])
def search_for_tag():
    if request.method == 'POST':
        tag_searched = request.form.get('tag_searched')
        tag_list = search_for_tag_request(tag_searched)
        return json.dumps(tag_list), 200
    return '', 400

@app.route('/watch/<video_id>', methods=['GET', 'POST'])
def watch(video_id):
    if request.method == 'POST':
        # print(request.form["cmmnt"])
        if "user" in session:
            add_comment_on_video(video_id, session["user"], request.form["cmmnt"])
        else:
            print("Error : tried to post comment without being connected")
        
    author_username, host_url, _ = get_author_info_from_video(video_id)
    reaction_result = get_reactions_on_video(video_id)
    nb_views = get_video_views(video_id)
    comments = get_comments_of_video(video_id)
    if nb_views == False : nb_views = 0
    green_state = 'green0'
    red_state   = 'red0'
    username = ''
    if "user" in session: 
        username = session["user"]
        add_view(username, video_id)
        like_state = get_user_has_liked_for_json(video_id, username)
        if like_state == 'like': green_state = 'green100'
        elif like_state == 'dislike' : red_state = 'red100'
    return render_template("html/watch.html", 
                           videoId = video_id, 
                           nb_likes = reaction_result["likes"], nb_dislikes = reaction_result["dislikes"], nb_views = nb_views,
                           name = author_username,
                           green_state = green_state, red_state = red_state,
                           hostURL = host_url,
                           comments = comments, lencomments = len(comments), connected = "user" in session, username = username,
                           is_following = get_if_follow_channel(username, author_username))

@app.route('/upload_pfp', methods=['GET', 'POST'])
def upload_pfp():
    if "user" in session: 
        if request.method == 'POST':
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
        return render_template("html/upload_pfp.html",
                               connected = "user" in session)
    return redirect(url_for('home'))

@app.route('/update_channel', methods=['GET', 'POST'])
def update_channel():
    if "user" in session: 
        if request.method == 'POST':
            new_channel_url = request.form["newchannelurl"]
            # to do : vérif user input ( != vide, ... ?)
            channel_info_resp = req.get(f"{new_channel_url}/channelinfo", timeout=5)
            if channel_info_resp.status_code == 200:
                resp_dict = channel_info_resp.json()
                is_user_an_author = False
                for video_id in resp_dict:
                    if resp_dict[video_id]["author"] != session["user"]:
                        continue
                    is_user_an_author = True
                    video_resp     = req.get(f"{new_channel_url}/video/{video_id}", timeout=5)
                    meta_resp      = req.get(f"{new_channel_url}/meta/{video_id}", timeout=5)
                    thumbnail_resp = req.get(f"{new_channel_url}/thumbnail/{video_id}", timeout=5)
                    if video_resp.status_code != 200 or meta_resp.status_code != 200 or thumbnail_resp.status_code != 200:
                        flash(f"{video_id} is not valid : video_resp={video_resp.status_code} , meta_resp={meta_resp.status_code} , thumbnail_resp={thumbnail_resp.status_code}")
                    else:
                        add_video(video_id, session["user"]) # Optimisable : faire une requete pour toute les vidéos au lieu de faire une requete par video
                if is_user_an_author :
                    update_channel_url(new_channel_url, session["user"])
                    flash(f"Update on {new_channel_url} successful !")
                else :
                    flash("You are not logged in with the right account : your server does not return your username.")
                    return render_template("html/update_channel.html",
                                           connected = "user" in session)
            else:
                flash(f"channel_info_resp.status_code == {channel_info_resp.status_code}")
        return render_template("html/update_channel.html",
                               connected = "user" in session)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # app.run(host='127.0.0.1', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
