import json
import os
from dotenv import load_dotenv
from data import youtube_utils
import random
from moviepy.editor import *
import subprocess
import webvtt
from datetime import datetime, timedelta

load_dotenv('/work/sheryl/merlot_reserve/.env')

with open("/work/sheryl/merlot_reserve/trims.json") as f:
    trims = json.load(f)

with open("/work/sheryl/siq2/siq2_qa_release/valid_ids.json") as f:
    valid_ids = json.load(f)

all_valid_ids = valid_ids["youtubeclips"] + valid_ids["movieclips"] + valid_ids["bmw"]


for id in os.listdir("/work/sheryl/full_videos"):
    if "mp3" in id or "FOWZ7B1QenY" in id or "DYvHB-9ehKM" in id:
        continue
    assert("mp4" in id)
    if id[:-4] not in trims:
        print(id, "not found")
        continue
    print(id)

    # trim mp4
    video_path = "/work/sheryl/full_videos"
    clip = VideoFileClip(os.path.join(video_path, id))
    trim_time = trims[id[:-4]]
    clip1 = clip.subclip(trim_time, 60+trim_time)
    clip1.write_videofile(os.path.join(video_path, id[:-4] + "_trim.mp4"),codec='libx264')

    # convert to mp3
    input_name = os.path.join(video_path, id[:-4] + "_trim.mp4")
    output_name = os.path.join(video_path, id[:-3] + "_trim.mp3")
    subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=output_name), shell=True)
    
    # download transcript
    transcript, info = youtube_utils.download_transcript(id[:-4], video_path)
    transcript = webvtt.read(os.path.join(video_path, id[:-4] + ".v2.en.vtt"))
    for caption in transcript:
        start_time = datetime.strptime(caption.start, '%H:%M:%S.%f')
        end_time = datetime.strptime(caption.end, '%H:%M:%S.%f')
        
        sec = int(str(trim_time).split(".")[0])
        ms = int(str(trim_time).split(".")[1])
        trim_timedelta = timedelta(seconds=sec, milliseconds=ms)
        new_start_time = (start_time + trim_timedelta).time()
        new_end_time = (end_time + trim_timedelta).time()
        caption.start = new_start_time.strftime("%H:%M:%S.%f")
        caption.end = new_end_time.strftime("%H:%M:%S.%f")
    transcript.save(os.path.join(video_path, id[:-4] + "_mod.vtt"))

    # download frames
    vid_name = id[:-4]
    frame_dir = os.path.join(os.environ["DATA_DIR"], "frames")
    if not os.path.exists(os.path.dirname(vid_name)):
        os.makedirs(os.path.join(frame_dir, vid_name), exist_ok=True)
        vid_path = os.path.join(os.environ["VIDEO_PATH"], id)
        output = os.path.join(frame_dir, vid_name, vid_name+"_%03d.jpg")
        subprocess.call('ffmpeg -i {video} -r 3 -q:v 1 {out_name}'.format(video=vid_path, out_name=output), shell=True)

    break
