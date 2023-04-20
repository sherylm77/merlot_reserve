import subprocess
import os
import random
from dotenv import load_dotenv

load_dotenv('/work/sheryl/merlot_reserve/.env')

mp4_files = os.listdir(os.environ["VIDEO_PATH"])

for file in mp4_files:
    input_name = os.path.join(os.environ["VIDEO_PATH"], file)
    output_name = os.path.join(os.environ["MP3_PATH"], file[:-3] + "mp3")
    subprocess.call('ffmpeg -i {video} -vn {out_name}'.format(video=input_name, out_name=output_name), shell=True)
