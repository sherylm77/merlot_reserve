from data import youtube_utils
import os
import json
import tempfile
import numpy as np

def find_active_videos(dataset_path):
    found_vids = []
    vids_path = os.path.join(dataset_path, "vision")
    qa_path = os.path.join(dataset_path, "qa")
    for id in os.listdir(qa_path):
        vid = id[:-3] + "mp4"
        temp_folder = tempfile.TemporaryDirectory()
        # vid_file_path = os.path.join(vids_path, "missing")
        result = youtube_utils.download_video(vid[:-4], temp_folder.name, True)
        video_found = result != None
        transcript, json_info = youtube_utils.download_transcript(vid[:-4], temp_folder.name)
        transcript_found = transcript != []
        if video_found and transcript_found:
            found_vids.append(vid[:-4])
        temp_folder.cleanup()
    return found_vids

yt_ids = find_active_videos("/work/sheryl/raw")
mv_ids = find_active_videos("/work/sheryl/movieclips/raw")
car_ids = find_active_videos("/work/sheryl/car/raw")

mv_ids_unique = np.setdiff1d(np.setdiff1d(np.array(mv_ids), np.array(yt_ids)),
                              np.array(car_ids))
car_ids_unique = np.setdiff1d(np.setdiff1d(np.array(car_ids), np.array(yt_ids)),
                              np.array(mv_ids))

for id in yt_ids:
    assert id not in mv_ids_unique and id not in car_ids_unique, id + " in yt and mv or car"
for id in mv_ids_unique:
    assert id not in car_ids_unique, id + " in mv and car"

valid_ids = {"youtubeclips": yt_ids, "movieclips": mv_ids_unique, "car": car_ids_unique}

with open("/work/sheryl/siq2/siq2_qa_release/valid_ids2.json", "w") as f:
    f.write(json.dumps(valid_ids))