from data import youtube_utils
import os
import json

dataset_path = "/work/sheryl/bmw/raw"

def find_active_videos(dataset_path):
    found_vids = []
    vids_path = os.path.join(dataset_path, "vision")
    qa_path = os.path.join(dataset_path, "qa")
    for id in os.listdir(qa_path):
        vid = id[:-3] + "mp4"
        vid_file_path = os.path.join(vids_path, "missing")
        result = youtube_utils.download_video(vid[:-4], vid_file_path, True)
        if result != None:
            found_vids.append(vid[:-4])
    return found_vids

yt_ids = find_active_videos("/work/sheryl/raw")
mv_ids = find_active_videos("/work/sheryl/movieclips/raw")
bmw_ids = find_active_videos("/work/sheryl/bmw/raw")

valid_ids = {"youtubeclips": yt_ids, "movieclips": mv_ids, "bmw": bmw_ids}

with open("/work/sheryl/merlot_reserve/valid_ids.json", "w") as f:
    f.write(json.dumps(valid_ids))