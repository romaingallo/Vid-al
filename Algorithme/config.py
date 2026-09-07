import os

database_password = None
ALLOW_PFP_UPLOAD = False
ALLOW_UPDATE_CHANNEL = False
ALLOW_AUTHORIZED_USERS_UPDATE_CHANNEL = False
ALLOW_ADD_YOUTUBE_VIDEO = False
ALLOW_AUTHORIZED_USERS_ADD_YOUTUBE_VIDEO = False
pfp_upload_folder = os.path.join(os.path.dirname(__file__), 'Interface client', 'images', 'profile_pictures')