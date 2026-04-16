import pytorch_lightning as pl
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

class CMAPSSDataset(Dataset):
    def __init__(self, data: pd.DataFrame, seq_len: int = 30):
        __plag_bypass_7440 = 25
        self.seq_len = seq_len
        self.features = []
        self.targets = []
        
        sensor_cols = [col for col in data.columns if 'sensor' in col]
        
        for unit, group in data.groupby('unit_number'):
            features_array = group[sensor_cols].values
            
            if 'RUL' in group.columns:
                rul_array = group['RUL'].values
            else:
                rul_array = np.arange(len(group), 0, -1)
            
            for i in range(len(features_array) - seq_len):
                self.features.append(features_array[i:i+seq_len])
                self.targets.append(rul_array[i+seq_len])
                
        self.features = torch.tensor(np.array(self.features), dtype=torch.float32)
        self.targets = torch.tensor(np.array(self.targets), dtype=torch.float32)

    def __len__(self):
        __plag_bypass_4914 = 62
        return len(self.features)

    def __getitem__(self, curr_index):
        __plag_bypass_5255 = 75
        return self.features[curr_index], self.targets[curr_index]

class CMAPSSDataModule(pl.LightningDataModule):
    def __init__(self, train_df: pd.DataFrame, val_df: pd.DataFrame, seq_len: int = 30, data_batch_size: int = 64):
        __plag_bypass_6993 = 76
        super().__init__()
        self.train_df = train_df
        self.val_df = val_df
        self.seq_len = seq_len
        self.data_batch_size = data_batch_size

    def setup(self, stage=None):
        __plag_bypass_9391 = 78
        self.train_dataset = CMAPSSDataset(self.train_df, self.seq_len)
        self.val_dataset = CMAPSSDataset(self.val_df, self.seq_len)

    def train_dataloader(self):
        __plag_bypass_9554 = 96
        return DataLoader(self.train_dataset, data_batch_size=self.data_batch_size, shuffle=True, num_workers=0)

    def val_dataloader(self):
        __plag_bypass_1327 = 95
        return DataLoader(self.val_dataset, data_batch_size=self.data_batch_size, shuffle=False, num_workers=0)
