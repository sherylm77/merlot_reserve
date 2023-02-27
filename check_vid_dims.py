import cv2
import os
from collections import Counter

vids_path = "/work/sheryl/siq2/vision"
heights = []
widths = []
resolution = []
for video in os.listdir(vids_path):
    vid = cv2.VideoCapture(os.path.join(vids_path, video))
    height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    heights.append(height)
    widths.append(width)
    resolution.append((width, height))

print(Counter(heights))
print(Counter(widths))
print(Counter(resolution))

