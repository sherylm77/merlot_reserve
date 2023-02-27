import librosa
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import os
from data import youtube_utils
import subprocess
import json

full_videos_path = "/work/sheryl/full_videos"
trimmed_audios_path = "/work/sheryl/movieclips/raw/acoustic"

trims = {}

videos_not_found = []

for audio in os.listdir(trimmed_audios_path):
    id = audio[:-4]
    if id in ["jRgTg1vu5vw", "WzDQEuf_Sdo"]: continue
    result = youtube_utils.download_video(id, full_videos_path, False)
    if result == None:
        videos_not_found.append(id)
        continue
    input_name = os.path.join(full_videos_path, id + ".mp4")
    full_audio_path = os.path.join(full_videos_path, id + ".mp3")
    subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=full_audio_path), shell=True)

    trimmed_audio_path = os.path.join(trimmed_audios_path, id + ".mp3")
    y_within, sr_within = librosa.load(full_audio_path)
    y_find, _ = librosa.load(trimmed_audio_path)

    window = 60

    c = signal.correlate(y_within, y_find[:sr_within*window], mode='valid', method='fft')
    peak = np.argmax(c)
    offset = round(peak / sr_within, 2)

    trims[id] = offset

with open("/work/sheryl/merlot_reserve/trims.json", "w") as f:
    f.write(json.dumps(trims))

print("VIDEOS NOT FOUND")
print(videos_not_found)
