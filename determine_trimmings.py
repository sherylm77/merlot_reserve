import librosa
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
import os
from data import youtube_utils
import subprocess
import json
import tempfile
from dotenv import load_dotenv

load_dotenv('/work/sheryl/merlot_reserve/.env')

trimmed_audios_path = "/work/sheryl/siq2/acoustic/mp3"

trims = {}

videos_not_found = []

valid_ids_path = os.path.join(os.environ["DATA_DIR"], "siq2_qa_release/valid_ids.json")
with open(valid_ids_path) as f:
    valid_ids = json.load(f)

all_valid_ids = valid_ids["youtubeclips"] + valid_ids["movieclips"] + valid_ids["car"]
for id in all_valid_ids:
    temp_folder = tempfile.TemporaryDirectory()
    result = youtube_utils.download_video(id, temp_folder.name, False)
    if result == None:
        videos_not_found.append(id)
        continue
    input_name = os.path.join(temp_folder.name, id + ".mp4")
    full_audio_path = os.path.join(temp_folder.name, id + ".mp3")
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
