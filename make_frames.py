import os
import subprocess

def video_to_frames(video_dir, data_dir):
    vid_names = os.listdir(video_dir)
    vid_names = ['2gmWndnOjL8.v2.en.vtt', 'Z81xJs0M5ZE.v2.en.vtt', 'p2S1qmGq6vI.v2.en.vtt', '8W4wakxQ_sk.v2.en.vtt', 'bSRNpcs0Pag.v2.en.vtt', 'UHvF1MNab6w.v2.en.vtt', 'rv5-4GhzrQc.v2.en.vtt', 'IkIwgpDeMgw.v2.en.vtt', 'FHOGplSy0fE.v2.en.vtt', 'l9g1XJukO14.v2.en.vtt', 'I-uzVZnE7cc.v2.en.vtt', 'XWL0SH8kUXg.v2.en.vtt', 'm2iJ3h-S5e0.v2.en.vtt', 'W2YIRSitQ5E.v2.en.vtt', 'qEma4PH-h_w.v2.en.vtt', 'HlG2vkYkZIk.v2.en.vtt', 'wk5CeHZP4Ls.v2.en.vtt', 'CiXTwfipyqk.v2.en.vtt', 'kIL3_tL8f20.v2.en.vtt', 'ceLlB7s6pHs.v2.en.vtt', 'rjuyyFsy7B0.v2.en.vtt', 'ZtBfr0Y5gGc.v2.en.vtt']
    frame_dir = os.path.join(data_dir, "frames")
    for vid in vid_names:
        # vid_name = os.path.splitext(vid)[0]
        vid_name = vid.split(".")[0]
        if not os.path.exists(os.path.dirname(vid_name)):
            os.makedirs(os.path.join(frame_dir, vid_name), exist_ok=True)
            # vid_path = os.path.join(video_dir, vid)
            vid_path = os.path.join(video_dir, vid_name + ".mp4")
            output = os.path.join(frame_dir, vid_name, vid_name+"_%03d.jpg")
            subprocess.call('ffmpeg -i {video} -r 3 -q:v 1 {out_name}'.format(video=vid_path, out_name=output), shell=True)

    print("Finished extracting frames.")
    
video_to_frames("/disk-1-data/siq2/vision", "/disk-1-data/siq2")