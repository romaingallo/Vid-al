

def convert_sql_output_to_list_for_card(data_input):
    # Input  : [(url0, user_pk, nb_likes, nb_view), (url1, user_pk, nb_likes, nb_view)]
    # Output : [
    #     {"channel": "Chaîne A", "views": "12k", "likes": "3" , "url": "video_test_00"},
    #     {"channel": "Chaîne B", "views": "4k" , "likes": "10", "url": "video_test_01"}
    # ]
    data_output = []
    for video_data in data_input:
        data_output.append({"channel": video_data[1], "views": str(video_data[3]), "likes": f"{video_data[2]}" , "url": video_data[0]})
    return data_output


def convert_sql_output_to_list_for_reactions(data_input):
    # Input  : [(is_dislike(False), nb_likes), (is_dislike(True), nb_dislikes), (is_dislike(None), nb_broken_likes)]
    # Output : [
    #     {"nb_likes": "12k", "nb_dislikes": "4k" }
    # ]
    data_output = {"likes" : data_input[0][1], "dislikes" : data_input[1][1]}
    return data_output