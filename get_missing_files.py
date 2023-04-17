from data import youtube_utils
import missing_files

siq_vid_file_path = "/work/sheryl/movieclips/raw/missing/vid"
siq_transcript_file_path = "/work/sheryl/movieclips/raw/missing/transcript"
car_vid_file_path = "/work/sheryl/car/raw/missing/vid"
car_transcript_file_path = "/work/sheryl/car/raw/missing/transcript"

# for vid_id in missing_files.siq_no_video:
#     youtube_utils.download_video(vid_id[:-4], siq_vid_file_path)

# for vid_id in missing_files.car_no_video:
#     youtube_utils.download_video(vid_id[:-16], car_vid_file_path)

for transcript_id in missing_files.siq_no_transcript:
    youtube_utils.download_transcript(transcript_id[:-4], siq_transcript_file_path)

# for transcript_id in missing_files.car_no_transcript:
#     youtube_utils.download_transcript(transcript_id[:-16], car_transcript_file_path)