import os
import json
import re
import subprocess
import sys
import random

sys.path.append("/work/sheryl")

# from raw import socialiq_std_folds

with open("/work/sheryl/siq2/siq2_qa_release/split2.json", "r") as f:
    all_vids = json.load(f)['subsets']

qa_files_not_found = []

def read_qa_in(dataset_path, vids, file_name, split):
    for vid in vids:
        vids_path = os.path.join(dataset_path, "vision")
        qa_path = os.path.join(dataset_path, "qa")
        vid_name = vid + ".mp4"
        vid_length = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration', '-of', 'default=noprint_wrappers=1:nokey=1', os.path.join(vids_path, vid_name)])

        vid_filename = os.path.join(qa_path, vid + ".txt")
        if not os.path.exists(vid_filename): 
            qa_files_not_found.append(vid)
            continue
        vid_file = open(vid_filename, "r") 

        file_end = False

        while not file_end:
            try:
                line = vid_file.readline()
            except:
                print(vid_filename)
                continue
            if not line:
                vid_file.close()
                break
            if bool(re.match(r"q\d+:*(.)", line.lower())):
                vid_dict = {}
                vid_dict["vid_name"] = vid
                vid_dict["ts"] = "0.00-" + vid_length.decode("utf-8").strip() # timestamp corresponding to question

                # question
                question_num = line.split(':')[0]
                str_list = line.split(':')[1:]
                question = ':'.join(str_list).strip()
                vid_dict['q'] = question
                qid = vid + "_" + question_num
                answer_num = 0
                correct_num = 0
                incorrect_num = 0
                all_correct_ans = []
                all_incorrect_ans = []
                while True:
                    pos = vid_file.tell()
                    next_line = vid_file.readline()
                    if not next_line:
                        vid_file.close()
                        file_end = True
                        break
                    if bool(re.match(r"a:*(.)", next_line.lower())):
                        # correct answer
                        ans_str_list = next_line.split(':')[1:]
                        answer = ':'.join(ans_str_list).strip()
                        if correct_num < 4 and answer not in all_correct_ans:
                            answer_num += 1
                            correct_num += 1
                            all_correct_ans.append(answer)
                    elif bool(re.match(r"i:*(.)", next_line.lower())):
                        # incorrect answer
                        ans_str_list = next_line.split(':')[1:]
                        answer = ':'.join(ans_str_list).strip()
                        if incorrect_num < 3 and answer not in all_incorrect_ans:
                            answer_num += 1
                            incorrect_num += 1
                            all_incorrect_ans.append(answer)
                    elif bool(re.match(r"c:*(.)", next_line.lower())):
                        continue
                    else:
                        # two answers - binary q&a task
                        q_count = 0
                        product = [[a, b] for a in all_correct_ans for b in all_incorrect_ans]
                        for answers in product: 
                            random.shuffle(answers)                           
                            vid_dict["a0"] = answers[0]
                            vid_dict["a1"] = answers[1]
                            vid_dict["qid"] = qid + "_" + str(q_count)
                            q_count += 1
                            if split != "test":
                                if answers[0] in all_correct_ans:
                                    vid_dict['answer_idx'] = 0
                                else:
                                    vid_dict['answer_idx'] = 1
                            else:
                                vid_dict["answer_idx"] = -1
                            file_name.write(json.dumps(vid_dict) + "\n")

                        vid_file.seek(pos)
                        break
    if qa_files_not_found != []:
        print("could not find these qa files: ", qa_files_not_found, "\n")


def make_json_for(split):
    qa_json_path = "/work/sheryl/merlot_reserve/qa_" + split + ".json"
    # vids = all_vids["youtubeclips"][split] + all_vids["movieclips"][split] + all_vids["car"][split] 
    qa_file_name = open(qa_json_path, "w")

    read_qa_in("/work/sheryl/raw", all_vids['youtubeclips'][split], qa_file_name, split)
    read_qa_in("/work/sheryl/movieclips/raw", all_vids['movieclips'][split], qa_file_name, split)
    read_qa_in("/work/sheryl/car/raw", all_vids['car'][split], qa_file_name, split)

    qa_file_name.close()

make_json_for('train')
make_json_for('val')
make_json_for('test')