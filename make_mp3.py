import subprocess
import os

def make_mp3_from(wav_folder, mp3_folder):
    wav_files = os.listdir(wav_folder)
    if not os.path.exists(mp3_folder):
        os.mkdir(mp3_folder)

    for wav in wav_files:
        input_name = os.path.join(wav_folder, wav)
        output_name = os.path.join(mp3_folder, wav[:-3] + "mp3")
        subprocess.call('ffmpeg -i {video} -ar 22050 -ac 1 {out_name}'.format(video=input_name, out_name=output_name), shell=True)
