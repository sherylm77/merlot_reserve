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

with open(os.environ["TRIMS_PATH"]) as f:
    trims = json.load(f)

valid_ids_path = os.path.join(os.environ["DATA_DIR"], "siq2_qa_release/valid_ids.json")
with open(valid_ids_path) as f:
    valid_ids = json.load(f)

all_valid_ids = valid_ids["youtubeclips"] + valid_ids["movieclips"] + valid_ids["car"]

full_videos_path = os.path.join(os.environ["DATA_DIR"], "full_videos")
if not os.path.exists(full_videos_path):
    os.mkdir(full_videos_path)

for id in all_valid_ids:
    if id not in trims:
        print(id, "not found")
        continue

    full_video = youtube_utils.download_video(id, full_videos_path, False)
    # trim mp4
    clip = VideoFileClip(full_video)
    trim_time = trims[id]
    clip1 = clip.subclip(trim_time, 60+trim_time)
    clip1.write_videofile(os.path.join(os.environ["VIDEO_PATH"], id + "_trim.mp4"),codec='libx264')

    # convert to mp3
    input_name = os.path.join(os.environ["VIDEO_PATH"], id + "_trim.mp4")
    output_name = os.path.join(os.environ["MP3_PATH"], id + "_trim.mp3")
    subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=output_name), shell=True)
    
    # download transcript
    transcript, info = youtube_utils.download_transcript(id, full_videos_path)
    transcript = webvtt.read(os.path.join(full_videos_path, id + ".v2.en.vtt"))
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
        # remove extra time stamps between <>
        caption.text = caption.text.replace("<.*?>", "")
    transcript.save(os.path.join(os.environ["TRANSCRIPT_PATH"], id + "_mod.vtt"))

    # download frames
    frame_dir = os.path.join(os.environ["DATA_DIR"], "frames_temp")
    if not os.path.exists(os.path.dirname(id)):
        os.makedirs(os.path.join(frame_dir, id), exist_ok=True)
        vid_path = os.path.join(os.environ["VIDEO_PATH"], id + "_trim.mp4")
        output = os.path.join(frame_dir, id, id+"_%03d.jpg")
        subprocess.call('ffmpeg -i {video} -r 3 -q:v 1 {out_name}'.format(video=vid_path, out_name=output), shell=True)

    break
