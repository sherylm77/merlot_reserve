import os
import json
import random
from sklearn.model_selection import train_test_split

with open("/work/sheryl/merlot_reserve/valid_ids.json") as f:
    valid_ids = json.load(f)

train_val_yt, test_yt = train_test_split(valid_ids["youtubeclips"], test_size=0.2, train_size=0.8)
train_yt, val_yt = train_test_split(train_val_yt, test_size=0.125, train_size=0.875)

train_val_mv, test_mv = train_test_split(valid_ids["movieclips"], test_size=0.2, train_size=0.8)
train_mv, val_mv = train_test_split(train_val_mv, test_size=0.125, train_size=0.875)

train_val_bmw, test_bmw = train_test_split(valid_ids["bmw"], test_size=0.2, train_size=0.8)
train_bmw, val_bmw = train_test_split(train_val_bmw, test_size=0.125, train_size=0.875)

split = {
        "subsets": 
            {    
                "youtubeclips": {"train": train_yt, "val": val_yt, "test": test_yt}, 
                "movieclips": {"train": train_mv, "val": val_mv, "test": test_mv}, 
                "bmw": {"train": train_bmw, "val": val_bmw, "test": test_bmw}
            }
        }

with open("/work/sheryl/merlot_reserve/split.json", "w") as f:
    f.write(json.dumps(split))