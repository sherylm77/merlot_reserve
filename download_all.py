# Given trims.json and valid_ids.json, downloads siq2 dataset audio (mp3 and wav),
# video, transcripts, and frames.

import json
import os
from dotenv import load_dotenv
from data import youtube_utils
import random
from moviepy.editor import *
import subprocess
import webvtt
import datetime
import tempfile

load_dotenv('/work/sheryl/merlot_reserve/.env')

with open(os.environ["TRIMS_PATH"]) as f:
    trims = json.load(f)

with open(os.environ["ORIGINAL_SPLIT_PATH"]) as f:
    split = json.load(f)

trim_not_found = []
videos_not_found = []
transcripts_not_found = []

def find_active_videos(ids):
    found_vids = []
    for id in ids:
        if id not in trims:
            trim_not_found.append(id)
            continue

        video_found = True
        transcript_found = True

        temp_folder = tempfile.TemporaryDirectory()

        full_video = youtube_utils.download_video(id, temp_folder.name, False)
        if full_video == None:
            video_found = False
            videos_not_found.append(id)
            continue

        # trim mp4
        if not os.path.exists(os.path.join(os.environ["VIDEO_PATH"], id + ".mp4")):
            clip = VideoFileClip(full_video)
            trim_time = trims[id]
            clip1 = clip.subclip(trim_time, 60+trim_time)
            clip1.write_videofile(os.path.join(os.environ["VIDEO_PATH"], id + ".mp4"),codec='libx264')

        if not os.path.exists(os.path.join(os.environ["MP3_PATH"], id + ".mp3")):
            # convert to mp3
            input_name = os.path.join(os.environ["VIDEO_PATH"], id + ".mp4")
            output_name = os.path.join(os.environ["MP3_PATH"], id + ".mp3")
            subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=output_name), shell=True)
        
        if not os.path.exists(os.path.join(os.environ["WAV_PATH"], id + ".wav")):
            # convert mp3 to wav
            input_name = os.path.join(os.environ["MP3_PATH"], id + ".mp3")
            output_name = os.path.join(os.environ["WAV_PATH"], id + ".wav")
            subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=output_name), shell=True)

        if not os.path.exists(os.path.join(os.environ["TRANSCRIPT_PATH"], id + ".vtt")):
            # download transcript
            transcript, info = youtube_utils.download_transcript(id, temp_folder.name)
            try:
                transcript = webvtt.read(os.path.join(temp_folder.name, id + ".v2.en.vtt"))
            except:
                try:
                    transcript = webvtt.read(os.path.join(temp_folder.name, id + ".v2.en-manual.vtt"))
                except:
                    transcript_found = False
                    transcripts_not_found.append(id)
                    continue
            trimmed_transcript = webvtt.WebVTT()

            # adjust start/end times to start at 0 instead of the trimmed time
            for caption in transcript:
                start_time = datetime.datetime.strptime(caption.start, '%H:%M:%S.%f')
                end_time = datetime.datetime.strptime(caption.end, '%H:%M:%S.%f')
                start_time = start_time.replace(year=2000,month=1,day=1)
                end_time = end_time.replace(year=2000,month=1,day=1)
                
                sec = int(str(trim_time).split(".")[0])
                ms = int(str(trim_time).split(".")[1])*1000 # convert millisecond to microsecond
                min = 0
                if sec >= 60:
                    min = sec // 60
                    sec = sec % 60
                trim_time_start = datetime.datetime.combine(datetime.date(year=2000,month=1,day=1), datetime.time(minute=min, second=sec, microsecond=ms))
                trim_time_end = datetime.datetime.combine(datetime.date(year=2000,month=1,day=1), datetime.time(minute=min, second=sec, microsecond=ms)) + datetime.timedelta(days=0, minutes=0, seconds=60)

                # remove extra time stamps between <>
                caption.text = caption.text.replace("<.*?>", "")
                if start_time >= trim_time_start and end_time <= trim_time_end:
                    caption.start = str(start_time - trim_time_start)
                    caption.end = str(end_time - trim_time_start)
                    trimmed_transcript.captions.append(caption)
            trimmed_transcript.save(os.path.join(os.environ["TRANSCRIPT_PATH"], id + ".vtt"))
            temp_folder.cleanup()

        # download frames
        frame_dir = os.path.join(os.environ["DATA_DIR"], "frames")
        if not os.path.exists(os.path.dirname(id)):
            os.makedirs(os.path.join(frame_dir, id), exist_ok=True)
            vid_path = os.path.join(os.environ["VIDEO_PATH"], id + ".mp4")
            output = os.path.join(frame_dir, id, id+"_%03d.jpg")
            subprocess.call('ffmpeg -i {video} -r 3 -q:v 1 {out_name}'.format(video=vid_path, out_name=output), shell=True)

        if video_found and transcript_found:
            found_vids.append(id)
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
with open(os.environ["CURRENT_SPLIT_PATH"], "w") as f:
    f.write(json.dumps(new_split))

if trim_not_found != []:
    print("could not find trims for:", trim_not_found)
if videos_not_found != []:
    print("could not download videos for:", videos_not_found)
if transcripts_not_found != []:
    print("could not download transcripts for:", transcripts_not_found)
