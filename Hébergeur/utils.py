from os import listdir
from os.path import isfile, join

def get_all_videos(folder_path):
    """Return a list of all videos id"""
    files_list = [f for f in listdir(folder_path) if isfile(join(folder_path, f))] # Select files in folder_path
    file_name_list = []
    for file_name in files_list:
        if '.json' in file_name:
            file_name_list.append(file_name.rsplit('.', 1)[0])
    return file_name_list