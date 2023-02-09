# Steps for setting up MERLOT Reserve on a TPU machine

- Clone this repo onto the TPU
- Set up environment
  - If using conda, make a conda environment from the siq_env.yml file
  - Otherwise install:
    - `python=3.8 tqdm numpy pyyaml scipy ipython cython typing h5py pandas matplotlib`
    - `pip install "jax[tpu]>=0.2.18" -f https://storage.googleapis.com/jax-releases/libtpu_releases.html`
    - `pip install -r requirements.txt`

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
