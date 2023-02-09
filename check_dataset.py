# checks if dataset has all the videos, transcripts, and qa files

import os
import numpy as np

dataset_folder = "/work/sheryl/bmw/raw"
transcripts = os.listdir(os.path.join(dataset_folder, "transcript"))
videos = os.listdir(os.path.join(dataset_folder, "vision"))

if "bmw" in dataset_folder:
    transcripts = [x[:-7] + "_trimmed.mp4.txt" for x in transcripts]
    videos = [x[:-12] + "_trimmed.mp4.txt" for x in videos]
else:
    transcripts = [x[:-7] + ".txt" for x in transcripts]
    videos = [x[:-12] + ".txt" for x in videos]
qa_files = os.listdir(os.path.join(dataset_folder, "qa"))

transcripts = np.array(transcripts)
videos = np.array(videos)
qa_files = np.array(qa_files)

print("qa", len(qa_files))

has_qa_no_vid = np.setdiff1d(qa_files, videos)
print("qa no vid")
print(has_qa_no_vid)
print(len(has_qa_no_vid))

has_qa_no_transcript = np.setdiff1d(qa_files, transcripts)
print("qa no transcript")
print(has_qa_no_transcript)
print(len(has_qa_no_transcript))

has_qa_no_vid_transcript = np.intersect1d(has_qa_no_vid, has_qa_no_transcript)
print("qa no vid or transcript")
print(has_qa_no_vid_transcript)
print(len(has_qa_no_vid_transcript))