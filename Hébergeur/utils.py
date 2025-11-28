from os import listdir
from os.path import isfile, join
import json

# def get_all_videos(folder_path):
#     """Return a list of all videos id"""
#     files_list = [f for f in listdir(folder_path) if isfile(join(folder_path, f))] # Select files in folder_path
#     file_name_list = []
#     for file_name in files_list:
#         if '.json' in file_name:
#             file_name_list.append(file_name.rsplit('.', 1)[0])
#     return file_name_list


def get_all_json(folder_path):
    """Return a list of all json files in the folder, in dictionary form."""
    all_files_list = [f for f in listdir(folder_path) if isfile(join(folder_path, f))] # Select files in folder_path
    json_files_dict = {}
    for file_name in all_files_list:
        if '.json' in file_name:
            print(f'{folder_path}\{file_name}')
            try:
                with open(f'{folder_path}\{file_name}', 'r', encoding='utf-8') as file:
                    file_dict = json.load(file)
                    json_files_dict[file_name.rsplit('.', 1)[0]] = file_dict
            except Exception as e : print("Error while reading json file : ", e)
    return json_files_dict