# merlot_reserve for SiQ
(Forked from Code release for "MERLOT Reserve: Neural Script Knowledge through Vision and Language and Sound")

## Download Pretrained Checkpoint
To download `base.ckpt` (needed for finetuning), run
```
cd merlot_reserve
python3 get_chkpt.py
```

## Set up
See https://sites.research.google/trc/about/ for more information on TPUs.

- If using conda, make a conda environment from the siq_env.yml file and activate the environment
- Also install:
  - `pip3 install "jax[tpu]>=0.2.18" -f https://storage.googleapis.com/jax-releases/libtpu_releases.html`

## Preprocessing SiQ 2.0
- Change paths in the .env file
- Change the path to the .env file in `merlot_reserve/finetune/tvqa/prep_data_siq2.py`
  - Change the file paths to the train and val data (split_fn)
    - Currently they are qa_train.json and qa_val.json
- Run `prep_data_siq2.py` by executing:
```
cd merlot_reserve/finetune/tvqa
./prep_data.sh
```

## Finetuning on SiQ 2.0
- Change the path to the .env file in `merlot_reserve/finetune/tvqa/siq2_finetune.py`
  - Change `config['data']['num_answers']` if needed
    - e.g. for binary task, this should be set to 2
  - Change TRAIN_SIZE
    - Number of lines in the qa_train.json file
  - Change wandb.init entity or set wandb to None
- Run `siq2_finetune.py` by executing:
```
cd merlot_reserve/finetune/tvqa
python3 siq2_finetune.py
```

## Information about MERLOT
MERLOT Reserve (in submission) is a model for learning joint representations of vision, language, and sound from YouTube. The learned model can be used in a zero-shot or finetuned setting, where it does well on tasks like VCR and TVQA.

Visit our project page at [rowanzellers.com/merlotreserve](https://rowanzellers.com/merlotreserve) or read the [full paper](#) to learn more.

## What's here

We are releasing the following:
* JAX code, and model checkpoints, for the MERLOT model
* Code for pretraining the model
* Code for finetuning the model on VCR and TVQA
* Code for doing zero-shot inference with the model

## Environment and setup

There are two different ways to run MERLOT Reserve:

* *Pretraining on videos* You'll need a TPU Pod VM for this. This step shouldn't be necessary for most people, as we have released model checkpoints.
* *Finetuning on VCR or TVQA* I've done this on a TPU v3-8 VM. This should be possible on GPU(s), but I haven't tested this on such hardware.
* *Zero-shot inference* I've ran this on a GPU (even an older, Titan X from 2016 works.)

### Installation on a GPU Machine
Install Cuda 11.4 (I used [this link](https://developer.download.nvidia.com/compute/cuda/11.4.2/local_installers/cuda-repo-ubuntu1804-11-4-local_11.4.2-470.57.02-1_amd64.deb)) and [CUDNN 8.2](https://developer.nvidia.com/rdp/cudnn-download). You might have to add something like this to your `PATH`:

`export LD_LIBRARY_PATH=/usr/local/cuda/lib64`

Create the environment:
```bash
conda create --name mreserve python=3.8 && conda activate mreserve
conda install -y python=3.8 tqdm numpy pyyaml scipy ipython cython typing h5py pandas matplotlib

# Install jax
pip install jax[cuda11_cudnn82] -f https://storage.googleapis.com/jax-releases/jax_releases.html
# If doing this on TPUs instead of locally...
# pip install "jax[tpu]>=0.2.18" -f https://storage.googleapis.com/jax-releases/libtpu_releases.html

# This is needed sometimes https://stackoverflow.com/questions/66060487/valueerror-numpy-ndarray-size-changed-may-indicate-binary-incompatibility-exp
pip uninstall numpy
pip install numpy==1.19.5

pip install -r requirements.txt
```

You can then try out the interactive script at [demo/demo_video.py](demo/demo_video.py). It will handle downloading the model checkpoint for you.

### Installation on a Cloud TPU VM

See the instructions in [pretrain/](pretrain/) to set up your environment on a TPU v3-8 VM.

## Checkpoints

These should get auto-downloaded if you use `PretrainedMerlotReserve` in [mreserve/modeling.py](mreserve/modeling.py). All are flax checkpoint files:

```bash
# pretrained checkpoints
gs://merlotreserve/ckpts/base
gs://merlotreserve/ckpts/base_resadapt
gs://merlotreserve/ckpts/large
gs://merlotreserve/ckpts/large_resadapt

# finetuned checkpoints
gs://merlotreserve/vcr_ckpts/vcr_finetune_base
gs://merlotreserve/vcr_ckpts/vcr_finetune_large

gs://merlotreserve/tvqa_ckpts/tvqa_finetune_base
gs://merlotreserve/tvqa_ckpts/tvqa_finetune_large

# TVQA Data
gs://merlotreserve/finetune_data/tvqa/

# VCR data
gs://merlotreserve/finetune_data/vcr/
```
