from flask import Flask, jsonify, request, send_file, redirect, url_for, session, render_template, flash
# from flask_cors import CORS
from database_requests import *
import config
import os
import threading
import time
from datetime import timedelta
from werkzeug.utils import secure_filename
import requests as req
import json
import hmac
import secrets
import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit, urlparse, parse_qs
from dotenv import load_dotenv
import re
from collections import defaultdict

INTERFACE_DIR = os.path.join(os.path.dirname(__file__), 'Interface client')
load_dotenv()
app = Flask(__name__, static_folder=INTERFACE_DIR, static_url_path='', template_folder=INTERFACE_DIR)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.permanent_session_lifetime = timedelta(minutes=5)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'Interface client', 'images', 'profile_pictures')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000 # max upload file size = 16 megabytes
# CORS(app)  # autorise toutes les origines (adapter en prod)

MAX_TAG_NUMBER_ON_VIDEO = 5
NUMBER_OF_VIDEO_PER_FETCH = 6 # -> le fecth javascript fait des offsets de 6, n'est pas lié à cette variable

LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_SECONDS = 15 * 60
login_attempts = {}
login_attempts_lock = threading.Lock()

YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

current_dir = os.path.dirname(os.path.abspath(__file__))

CSRF_SESSION_KEY = '_csrf_token'

def validate_public_server_url(value):
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password:
            return None
        if parsed.path not in {'', '/'} or parsed.query or parsed.fragment:
            return None
        hostname = parsed.hostname
        if not hostname or len(hostname) > 253:
            return None
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            return None

        addresses = socket.getaddrinfo(
            hostname,
            port or (443 if parsed.scheme == 'https' else 80),
            type=socket.SOCK_STREAM,
        )
        if not addresses or any(
            not ipaddress.ip_address(address[4][0]).is_global for address in addresses
        ):
            return None

        return urlunsplit((parsed.scheme, parsed.netloc, '', '', '')).rstrip('/')
    except (AttributeError, ValueError, socket.gaierror, UnicodeError):
        return None

def get_from_public_server(base_url, path):
    return req.get(f'{base_url}{path}', timeout=5, allow_redirects=False)

def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if token is None:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token

USERNAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{0,31}$")
TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,49}$")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_username(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or len(value) > 32:
        return None
    if any(ch.isspace() for ch in value):
        return None
    if not USERNAME_RE.fullmatch(value):
        return None
    return value

def sanitize_tag_name(value):
    if value is None:
        return None
    value = str(value).strip()
    if not value or len(value) > 50:
        return None
    if CONTROL_CHARS_RE.search(value):
        return None
    if any(ch in value for ch in [';', '\'', '"', '\\', '--']):
        return None
    if not TAG_RE.fullmatch(value):
        return None
    return value

def sanitize_comment_text(value, max_length=1000):
    if value is None:
        return ""
    text = str(value).strip()
    text = CONTROL_CHARS_RE.sub('', text)
    if len(text) > max_length:
        text = text[:max_length]
    return text

def sanitize_generic_text(value, max_length=255):
    if value is None:
        return None
    value = str(value).strip()
    if not value or len(value) > max_length:
        return None
    if CONTROL_CHARS_RE.search(value):
        return None
    if any(ch in value for ch in [';', '\'', '"', '\\', '--']):
        return None
    return value

@app.context_processor
def inject_csrf_token():
    return {'csrf_token': get_csrf_token()}

@app.context_processor
def inject_config():
    authorized_user_to_add_youtube_video = config.ALLOW_ADD_YOUTUBE_VIDEO
    if "user" in session and config.ALLOW_AUTHORIZED_USERS_ADD_YOUTUBE_VIDEO: 
        authorized_user_to_add_youtube_video = can_user_add_youtube_video(session["user"])
    return {'ALLOW_ADD_YOUTUBE_VIDEO': authorized_user_to_add_youtube_video}

@app.before_request
def protect_state_changing_requests():
    if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return

    submitted_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
    expected_token = session.get(CSRF_SESSION_KEY)
    if not expected_token or not submitted_token or not hmac.compare_digest(submitted_token, expected_token):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Invalid CSRF token.'}), 400
        return 'Invalid CSRF token.', 400

rate_limit = defaultdict(list)

def is_rate_limited(ip):
    now = time.time()
    history = rate_limit[ip]
    history[:] = [t for t in history if now - t < 60]
    if len(history) >= 10:
        return True
    history.append(now)
    return False

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

def login_is_rate_limited(ip_address, username):
    now = time.monotonic()
    keys = [('ip', ip_address), ('user', ip_address, username)]
    with login_attempts_lock:
        for key in keys:
            attempts = [timestamp for timestamp in login_attempts.get(key, [])
                        if now - timestamp < LOGIN_WINDOW_SECONDS]
            login_attempts[key] = attempts
            if len(attempts) >= LOGIN_MAX_FAILURES:
                retry_after = int(LOGIN_WINDOW_SECONDS - (now - attempts[0])) + 1
                return retry_after
    return 0

def record_login_failure(ip_address, username):
    now = time.monotonic()
    keys = [('ip', ip_address), ('user', ip_address, username)]
    with login_attempts_lock:
        for key in keys:
            attempts = [timestamp for timestamp in login_attempts.get(key, [])
                        if now - timestamp < LOGIN_WINDOW_SECONDS]
            attempts.append(now)
            login_attempts[key] = attempts

def clear_login_failures(ip_address, username):
    with login_attempts_lock:
        login_attempts.pop(('user', ip_address, username), None)

@app.route('/')
def home():
    # path = os.path.join(os.path.dirname(__file__), '.', 'Interface client', 'main.html')
    # return send_file(os.path.abspath(path))
    return render_template('html/main.html',
                           connected = "user" in session)

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = sanitize_username(request.form.get("usrname", ""))
        password = request.form.get("psswrd", "")
        if username is None or len(password) < 6 or len(password) > 256:
            flash("Invalid password or username.")
            return redirect(url_for('login'))
        ip_address = request.remote_addr or "unknown"
        retry_after = login_is_rate_limited(ip_address, username)
        if retry_after:
            response = redirect(url_for('login'))
            response.headers["Retry-After"] = str(retry_after)
            flash("Too many failed login attempts. Please try again later.")
            return response, 429

        if authentification(username, password) :
            clear_login_failures(ip_address, username)
            session["user"] = username
            session.permanent = True
            return redirect(url_for('home'))
        else :
            record_login_failure(ip_address, username)
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
        username_input = sanitize_username(request.form.get("usrname", ""))
        password_input = request.form.get("psswrd", "")
        if username_input is None or len(password_input) < 6 or len(password_input) > 256:
            flash("Invalid entry : the username should not be empty, and the password should be at least 6 characters.")
            return redirect(url_for('register'))
        elif len(get_user_by_name(username_input)) > 0 :
            flash("Username already taken.")
            return redirect(url_for('register'))
        else : # adding user + session
            add_new_user(username_input, password_input)
            flash("User created, you can now log in.")
            print("New user created : ", username_input)
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
    if not offset.isnumeric() : return '', 400
    NUMBER_OF_VIDEO_PER_FETCH = 6
    if "user" in session: 
        data = get_videos(session["user"], NUMBER_OF_VIDEO_PER_FETCH, int(offset))
    else:
        data = get_videos(False, NUMBER_OF_VIDEO_PER_FETCH, int(offset))
    return jsonify(data)

@app.route('/api/channel/<channelId>/<offset>')
def channel(channelId, offset):
    if not offset.isnumeric() : return '', 400
    NUMBER_OF_VIDEO_PER_FETCH = 6
    data = get_all_videos_from_channel(channelId, NUMBER_OF_VIDEO_PER_FETCH, int(offset))
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
            comment_id = sanitize_generic_text(request.form.get('comment_id'))
            if not comment_id : return '', 400
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
        pfp_path = os.path.join(images_dir, f'{secure_filename(session["user"])}.jpg')
        minetype = 'image/jpeg'
        if not os.path.exists(pfp_path):
            pfp_path = os.path.join(images_dir, f'{secure_filename(session["user"])}.png')
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
    username = secure_filename(username)
    images_dir = os.path.join(current_dir, 'Interface client', 'images', 'profile_pictures')
    pfp_path = os.path.join(images_dir, f'{username}.jpg')
    minetype = 'image/jpeg'
    if not os.path.exists(pfp_path): 
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
        authorized_user_to_update_channel = config.ALLOW_UPDATE_CHANNEL
        if config.ALLOW_AUTHORIZED_USERS_UPDATE_CHANNEL: authorized_user_to_update_channel = can_user_update_channel(session["user"])
        return render_template("html/visit_channel.html", 
                                   name=channel_name, 
                                   own_profile= session["user"] == channel_name, 
                                   hostURL=host_url,
                                   connected = "user" in session,
                                   is_following = get_if_follow_channel(session["user"], channel_name),
                                    ALLOW_PFP_UPLOAD = config.ALLOW_PFP_UPLOAD,
                                    ALLOW_UPDATE_CHANNEL = authorized_user_to_update_channel)
    return render_template("html/visit_channel.html", 
                           name=channel_name, 
                           own_profile=False, 
                           hostURL=host_url,
                           connected = "user" in session,
                           ALLOW_PFP_UPLOAD = config.ALLOW_PFP_UPLOAD,
                           ALLOW_UPDATE_CHANNEL = config.ALLOW_UPDATE_CHANNEL)

@app.route('/api/followedvideos/<offset>')
def followedvideos(offset):
    if "user" in session : 
        NUMBER_OF_VIDEO_PER_FETCH = 6
        data = get_followed_videos(session["user"], NUMBER_OF_VIDEO_PER_FETCH, int(offset))
        return jsonify(data), 200
    return jsonify({"error": 'User Unauthorized'}), 401

@app.route('/api/togglefollowing', methods=['POST'])
def togglefollowing():
    if request.method == 'POST':
        if "user" in session : 
            channel_followed_username = sanitize_username(request.form.get('channel_followed_username'))
            if not channel_followed_username :
                return jsonify({"error": "channel_followed_username is missing."}), 400
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
    if not "user" in session:
        return redirect(url_for('home'))
    if not session["user"] == channel_name:
        return redirect(url_for('home'))
    
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
            video_id = sanitize_generic_text(request.form.get('video_id'), 255)
            if not video_id : return '', 400
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
            video_id = sanitize_generic_text(request.form.get('video_id'), 255)
            if not video_id : return '', 400
            if is_video_from(video_id, session["user"]):
                tag_name = sanitize_tag_name(request.form.get('tag_name'))
                if not tag_name : return '', 400
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
            video_id = sanitize_generic_text(request.form.get('video_id'), 255)
            if not video_id : return '', 400
            if is_video_from(video_id, session["user"]):
                list_tags_on_video = get_tags_of_video(video_id)
                if len(list_tags_on_video)+1 > MAX_TAG_NUMBER_ON_VIDEO: return jsonify({"error": f'The video has already been tagged {MAX_TAG_NUMBER_ON_VIDEO} times (max per video).'}), 500
                tag_name = sanitize_tag_name(request.form.get('tag_name'))
                if not tag_name : return '', 400
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
        tag_searched = sanitize_tag_name(request.form.get('tag_searched'))
        if not tag_searched : return '', 400
        tag_list = search_for_tag_request(tag_searched)
        return json.dumps(tag_list), 200
    return '', 400

@app.route('/watch/<video_id>', methods=['GET', 'POST'])
def watch(video_id):
    if not sanitize_generic_text(video_id, 255) : return redirect(url_for('home'))
    if not is_video_in_db(video_id) : return redirect(url_for('home'))

    is_youtube_video = get_is_youtube_video(video_id)
    if request.method == 'POST':
        # print(request.form["cmmnt"])
        if "user" in session:
            comment_text = sanitize_comment_text(request.form.get("cmmnt", ""))
            if comment_text:
                add_comment_on_video(video_id, session["user"], comment_text)
        else:
            print("Error : tried to post comment without being connected")
        
    username = ''
    green_state = 'green0'
    red_state   = 'red0'
    if not is_youtube_video:
        author_username, host_url, _ = get_author_info_from_video(video_id)
        reaction_result = get_reactions_on_video(video_id)
        nb_views = get_video_views(video_id)
        comments = get_comments_of_video(video_id)
        is_following = get_if_follow_channel(username, author_username)
        if nb_views == False : nb_views = 0
    else :
        author_username, host_url = "author_username", "host_url"
        reaction_result = {"likes" : "likes", "dislikes" : "dislikes"}
        nb_views = "nb_views"
        comments = []
        is_following = False
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
                           is_following = is_following,
                           is_youtube_video = is_youtube_video)

@app.route('/upload_pfp', methods=['GET', 'POST'])
def upload_pfp():

    if not config.ALLOW_PFP_UPLOAD:
        flash("ALLOW_PFP_UPLOAD = False")
        return redirect(url_for('home'))

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
                # check file size (max 2MB)
                try:
                    # seek to end to get size, then rewind
                    file.stream.seek(0, os.SEEK_END)
                    file_size = file.stream.tell()
                    file.stream.seek(0)
                except Exception:
                    file_size = None
                MAX_SIZE = 2 * 1024 * 1024
                if file_size is not None and file_size > MAX_SIZE:
                    flash('File is too large. Max size is 2 MB.')
                    return redirect(request.url)
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

    authorized_user_to_update_channel = config.ALLOW_UPDATE_CHANNEL
    if "user" in session and config.ALLOW_AUTHORIZED_USERS_UPDATE_CHANNEL: 
        authorized_user_to_update_channel = can_user_update_channel(session["user"])
    if not authorized_user_to_update_channel:
        flash("authorized_user_to_update_channel = False")
        return redirect(url_for('home'))

    if "user" in session: 
        if request.method == 'POST':
            new_channel_url = validate_public_server_url(request.form.get("newchannelurl", ""))
            if not new_channel_url:
                flash("Invalid server URL. Use a public HTTP(S) server URL without a path or credentials.")
                return render_template("html/update_channel.html",
                                       connected = "user" in session)

            channel_info_resp = get_from_public_server(new_channel_url, "/channelinfo")
            if channel_info_resp.status_code == 200:
                resp_dict = channel_info_resp.json()
                is_user_an_author = False
                for video_id in resp_dict:
                    if resp_dict[video_id]["author"] != session["user"]:
                        continue
                    is_user_an_author = True
                    video_resp     = get_from_public_server(new_channel_url, f"/video/{video_id}")
                    meta_resp      = get_from_public_server(new_channel_url, f"/meta/{video_id}")
                    thumbnail_resp = get_from_public_server(new_channel_url, f"/thumbnail/{video_id}")
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

def normalize_youtube_id(value):
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    if "youtube.com" in value or "youtu.be" in value:
        try:
            parsed = urlparse(value)
            if "youtu.be" in parsed.netloc:
                video_id = parsed.path.strip("/")
                return video_id if YOUTUBE_ID_RE.fullmatch(video_id) else None

            if "youtube.com" in parsed.netloc:
                qs = parse_qs(parsed.query)
                video_id = qs.get("v", [None])[0]
                return video_id if video_id and YOUTUBE_ID_RE.fullmatch(video_id) else None
        except Exception:
            return None

    return value if YOUTUBE_ID_RE.fullmatch(value) else None

@app.route('/add_youtube_video', methods=['GET', 'POST'])
def add_youtube_video():

    authorized_user_to_add_youtube_video = config.ALLOW_ADD_YOUTUBE_VIDEO
    if "user" in session and config.ALLOW_AUTHORIZED_USERS_ADD_YOUTUBE_VIDEO: 
        authorized_user_to_add_youtube_video = can_user_add_youtube_video(session["user"])
    if not authorized_user_to_add_youtube_video:
        flash("authorized_user_to_add_youtube_video = False")
        return redirect(url_for('home'))

    if request.method == 'POST':

        if is_rate_limited(request.remote_addr):
            flash("To many requests, try later.")
            return render_template("html/add_youtube_video.html")
        
        video_id = normalize_youtube_id(request.form.get("youtubevideoid"))
        if not video_id:
            flash("ID YouTube invalide.")
            return render_template("html/add_youtube_video.html")
        # video_input_id = request.form["youtubevideoid"]
        # if not video_input_id: 
        #     flash(f"Invalid post...")
        #     return render_template('html/add_youtube_video.html')
        # if len(video_input_id)>11: # si url complete
        #     first_split = video_input_id.split("?v=", 1)
        #     second_split = first_split[1].split("&", 1)
        #     video_input_id = second_split[0]

        if is_video_in_db(video_id):
            flash("This video is already registered.")
            return render_template("html/add_youtube_video.html")


        video_info_resp = req.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            timeout=5,
            allow_redirects=False)
        
        if video_info_resp.status_code != 200:
            flash(f"Video not found...")
            return render_template('html/add_youtube_video.html')

        content_type = video_info_resp.headers.get("Content-Type", "")
        if "application/json" not in content_type and not video_info_resp.text.strip().startswith("{"):
            flash("Réponse invalide du service externe.")
            return render_template("html/add_youtube_video.html")

        payload = video_info_resp.json()
        author_name = payload.get("author_name")
        author_url = payload.get("author_url")
        if not author_name or not author_url:
            flash("Données YouTube incomplètes.")
            return render_template("html/add_youtube_video.html")
        
        insert_succesfull = insert_new_youtube_video(video_id)
        # print(video_info_resp.json())
        if insert_succesfull :
            flash(f"Video added !")
            # author_name = video_info_resp.json()['author_name']
            # author_url  = video_info_resp.json()['author_url']
            # print(author_name)
            # print("youtuber_pfp_in_db", youtuber_pfp_in_db(author_name, app.config['UPLOAD_FOLDER']))
            if not youtuber_pfp_in_db(author_name, app.config['UPLOAD_FOLDER']):
                if not get_youtuber_pfp_from_video_id(author_name, author_url, app.config['UPLOAD_FOLDER']):
                    flash(f"Video added, but the profile picture wasn't loaded.")
        else:
            flash(f"Video insert failed...")

        return render_template('html/add_youtube_video.html')
    else:
        return render_template('html/add_youtube_video.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if "user" in session : 
        if request.method == 'POST':
            new_like_scale = request.form.get('new_like_scale')
            if new_like_scale is not None:
                try:
                    new_like_scale = float(new_like_scale)
                except (TypeError, ValueError):
                    return jsonify({"error": 'Invalid value.'}), 400
                if update_user_setting("setting_like_scale", new_like_scale, session["user"]):
                    return '', 200
                return jsonify({"error": 'Update failed.'}), 500
            new_view_scale = request.form.get('new_view_scale')
            if new_view_scale is not None:
                try:
                    new_view_scale = float(new_view_scale)
                except (TypeError, ValueError):
                    return jsonify({"error": 'Invalid value.'}), 400
                if update_user_setting("setting_view_scale", new_view_scale, session["user"]):
                    return '', 200
                return jsonify({"error": 'Update failed.'}), 500
            new_tag_scale = request.form.get('new_tag_scale')
            if new_tag_scale is not None:
                try:
                    new_tag_scale = float(new_tag_scale)
                except (TypeError, ValueError):
                    return jsonify({"error": 'Invalid value.'}), 400
                if update_user_setting("setting_tags_scale", new_tag_scale, session["user"]):
                    return '', 200
                return jsonify({"error": 'Update failed.'}), 500
            return '', 400
        
        list_settings = get_user_setting(session["user"])
        list_tags     = get_user_followed_tags(session["user"])
        return render_template("html/settings.html",
                               list_settings = list_settings,
                               list_tags = list_tags)
    return jsonify({"error": 'Unauthenticated user'}), 401

@app.route('/api/settings/remove_followed_tag', methods=['POST'])
def remove_followed_tag():
    if request.method == 'POST':
        if "user" in session: 
            tag_name = sanitize_tag_name(request.form.get('tag_name'))
            if not tag_name : return '', 400
            if remove_followed_tag_from_user(tag_name, session["user"]):
                return '', 200
            else : return jsonify({"error": f'Internal error when deletion of tag {tag_name}'}), 500
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

@app.route('/api/settings/add_user_followed_tag', methods=['POST'])
def add_user_followed_tag():
    if request.method == 'POST':
        if "user" in session: 
            tag_name = sanitize_tag_name(request.form.get('tag_name'))
            if not tag_name : return '', 400
            list_followed_tags = get_user_followed_tags(session["user"])
            if tag_name in list_followed_tags: return jsonify({"error": f'You are already following the tag {tag_name}.'}), 500
            if add_tag_for_user_followed(tag_name, session["user"]):
                return '', 200
            else : return jsonify({"error": f'Internal error when adding tag {tag_name}'}), 500
        else:
            return jsonify({"error": 'User Unauthorized'}), 401
    return '', 400

if __name__ == '__main__':
    # app.run(host='127.0.0.1', port=5000, debug=True)
    config.database_password = os.environ["DATABASE_PASSWORD"]

    app.run(host='0.0.0.0', port=5000, debug=True)
