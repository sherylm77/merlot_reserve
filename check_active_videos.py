from data import youtube_utils
import os
import json
import tempfile

def find_active_videos(dataset_path):
    found_vids = []
    vids_path = os.path.join(dataset_path, "vision")
    qa_path = os.path.join(dataset_path, "qa")
    for id in os.listdir(qa_path):
        vid = id[:-3] + "mp4"
        vid_file_path = os.path.join(vids_path, "missing")
        result = youtube_utils.download_video(vid[:-4], vid_file_path, True)
        video_found = result != None
        temp_folder = tempfile.TemporaryDirectory()
        transcript, json_info = youtube_utils.download_transcript(vid[:-4], temp_folder.name)
        transcript_found = transcript != []
        if video_found and transcript_found:
            found_vids.append(vid[:-4])
        temp_folder.cleanup()
    return found_vids

yt_ids = find_active_videos("/work/sheryl/raw")
mv_ids = find_active_videos("/work/sheryl/movieclips/raw")
bmw_ids = find_active_videos("/work/sheryl/bmw/raw")

valid_ids = {"youtubeclips": yt_ids, "movieclips": mv_ids, "bmw": bmw_ids}

with open("/work/sheryl/merlot_reserve/valid_ids.json", "w") as f:
    f.write(json.dumps(valid_ids))