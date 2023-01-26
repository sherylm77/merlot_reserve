# runs make_mp3.py, make_frames.py, make_json.py to preprocess data for SiQ 1.0
# fill in correct paths in .env

import subprocess
import os
import argparse
import make_mp3
import make_frames
import make_json
from dotenv import load_dotenv

load_dotenv('../../.env')

parser = argparse.ArgumentParser()
parser.add_argument(
    '--mp3',
    help='file path for wav files to convert to mp3',
    action='store_true'
)
parser.add_argument(
    '--frames',
    help='file path for videos to convert to frames',
    action='store_true'
)
parser.add_argument(
    '--json',
    help='file path for qa to convert to train/val json files',
    action='store_true'
)
parser.add_argument('--binary', 
    help='for making json only; if the task is binary q&a',
    action='store_true'
)

args = parser.parse_args()

if args.mp3:
    make_mp3_from(os.environ["WAV_PATH"])

if args.frames:
    video_to_frames(os.environ["VIDEO_PATH"])

if args.json:
    # make json for train vids
    make_json_for(os.environ["TRAIN_VIDS_PATH"], 
                os.path.join(os.environ["DATA_DIR"], "siq1_train.jsonl"), 
                os.environ["QA_PATH"], args.binary)
    # make json for val vids
    make_json_for(os.environ["VAL_VIDS_PATH"], 
                os.path.join(os.environ["DATA_DIR"], "siq1_val.jsonl"), 
                os.environ["QA_PATH"], args.binary)
