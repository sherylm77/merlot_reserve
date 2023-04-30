# Steps for setting up MERLOT Reserve on a TPU machine

- Clone this repo onto the TPU
- Set up environment
  - If using conda, make a conda environment from the siq_env.yml file and activate the environment
  - Also install:
    - `pip3 install "jax[tpu]>=0.2.18" -f https://storage.googleapis.com/jax-releases/libtpu_releases.html`

# Finetuning on SiQ 1.0
## Preprocessing SiQ 1.0
- Unzip the siq1.zip file
- The folder is organized into the following structure:
```
raw
|_ acoustic
|  |_ covarep
|  |_ wav
|_ qa
|_ siq_qa_release 
|_ transcript 
|_ vision 
```
- Run prep_siq1.py and put the correct flags for mp3, frames, and json
  - If you don’t have mp3 files, set the flag to generate them from wav
  - If you don’t have frames, set the flag to generate them from mp4
  - If you don’t have the json files siq1_train.jsonl and siq1_val.jsonl, set the flag
- Run prep_data.sh
  - This runs prep_data_siq.py
  - Input the num_folds and num_folds_val in the shell script
    - For example, for siq1 (multiple choice task) the numbers were 64 and 8 respectively
    - This is the number of output tfrecord files
- Change paths in the .env file
- Download base pretrained checkpoint by running get_chkpt.py

## Finetune on SiQ 1.0
- Run siq_finetune.py
  - Change the path to the .env file
  - Change config['data']['num_answers'] if needed
    - e.g. for binary task, this should be set to 2
  - Change TRAIN_SIZE
    - Number of lines in the siq1_train.jsonl file
  - Change wandb.init entity or set wandb to None

# Finetuning on SiQ 2.0
## Get SiQ 2.0 data
- Unzip the siq2.zip file
- The folder is organized into the following structure:
```
raw
|_ acoustic
|  |_ mp3
|  |_ wav
|_ frames
|_ qa
|_ siq2_qa_release 
|  |_ qa_train.json
|  |_ qa_val.json
|  |_ qa_test.json
|  |_ split.json
|  |_ valid_ids.json
|_ transcript 
|_ vision 
```
- If you don't have access to the SiQ 2.0 data zip file, make a siq2 directory with subdirectories like this:
```
siq2
|_ acoustic
|  |_ mp3
|_ siq2_qa_release 
|  |_ qa_train.json
|  |_ qa_val.json
|  |_ qa_test.json
|  |_ split.json
|  |_ valid_ids.json
|  |_ trims.json
|_ transcript 
|_ vision 
```
  - You can copy over the siq2_qa_release directory from this repo
  - Update paths in the .env file found in merlot_reserve
  - Update the path to the .env file in merlot_reserve/download_all.py
  - Run download_all.py

## Preprocessing SiQ 2.0
- Run prep_data.sh
  - Make sure the command runs prep_data_siq2.py
  - Input the num_folds and num_folds_val in the shell script
    - For example, for siq2 (binary task) the numbers were 128 and 16 respectively
    - This is the number of output tfrecord files
  - Change paths in the .env file
  - Change the path to the .env file in prep_data_siq2.py
  - Change the file paths to the train and val data (split_fn)
    - Currently they are qa_train.json and qa_val.json
- Download base pretrained checkpoint by running get_chkpt.py

## Finetune on SiQ 2.0
- Run siq2_finetune.py
  - Change the path to the .env file in siq2_finetune.py
  - Change config['data']['num_answers'] if needed
    - e.g. for binary task, this should be set to 2
  - Change TRAIN_SIZE
    - Number of lines in the qa_train.json file
  - Change wandb.init entity or set wandb to None
