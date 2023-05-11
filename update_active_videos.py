from data import youtube_utils
import os
import json
import tempfile
from dotenv import load_dotenv

load_dotenv('/work/sheryl/merlot_reserve/.env')

# load train-val-test split from json file
with open(os.environ["SPLIT_PATH"]) as f:
    split = json.load(f)

# given a list of video ids, return a list of ids that have active videos and
# transcripts on youtube
def find_active_videos(ids):
    found_vids = []
    for id in ids:
        temp_folder = tempfile.TemporaryDirectory()
        result = youtube_utils.download_video(id, temp_folder.name, True)
        video_found = result != None
        transcript, json_info = youtube_utils.download_transcript(id, temp_folder.name)
        transcript_found = transcript != []

        if video_found and transcript_found:
            found_vids.append(id)
        temp_folder.cleanup()
    return found_vids

yt_clips = split['subsets']['youtubeclips']
mv_clips = split['subsets']['movieclips']
car_clips = split['subsets']['car']
new_split = {
        "subsets":
            {    
                "youtubeclips": {"train": find_active_videos(yt_clips['train']), "val": find_active_videos(yt_clips['val']), "test": find_active_videos(yt_clips['test'])}, 
                "movieclips": {"train": find_active_videos(mv_clips['train']), "val": find_active_videos(mv_clips['val']), "test": find_active_videos(mv_clips['test'])}, 
                "car": {"train": find_active_videos(car_clips['train']), "val": find_active_videos(car_clips['val']), "test": find_active_videos(car_clips['test'])}
            }
        }

# put updated split into json file
with open("/work/sheryl/siq2/siq2_qa_release/split_new.json", "w") as f:
    f.write(json.dumps(new_split))