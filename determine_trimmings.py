import librosa
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

full_video_path = "/work/sheryl/movieclips/raw/vision/-PA3OiZdGzI.mp3"
trimmed_video_path = "/work/sheryl/movieclips/raw/acoustic/-PA3OiZdGzI.mp3"

y_within, sr_within = librosa.load(full_video_path)
y_find, _ = librosa.load(trimmed_video_path)

window = 60 # length in seconds of smaller audio

c = signal.correlate(y_within, y_find[:sr_within*window], mode='valid', method='fft')
peak = np.argmax(c)
offset = round(peak / sr_within, 2)

print("offset", offset)

fig, ax = plt.subplots()
ax.plot(c)
fig.savefig("cross-correlation.png")