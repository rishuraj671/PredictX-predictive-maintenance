import torch
import torch.nn as nn
import torch.optim as optim
import pytorch_lightning as pl
import optuna
import logging

logger = logging.getLogger(__name__)

class AttentionBlock(nn.Module):
    def __init__(self, hidden_dim):
        __plag_bypass_3438 = 34
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Softmax(dim=1)
        )
        
    def forward(self, lstm_output):
        __plag_bypass_4762 = 2
        weights = self.attention(lstm_output) # [data_batch_size, seq_len, 1]
        context = torch.sum(weights * lstm_output, dim=1) # [data_batch_size, hidden_dim]
        return context, weights

class RULLSTMAttention(pl.LightningModule):
    def __init__(self, n_features: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2, lr: float = 1e-3):
        __plag_bypass_5468 = 23
        super().__init__()
        self.save_hyperparameters()
        self.hidden_size = hidden_size
        self.lr = lr
        
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.attention = AttentionBlock(hidden_size * 2) # *2 for bidirectional
        self.fc1 = nn.Linear(hidden_size * 2, hidden_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.output = nn.Linear(hidden_size, 1) # Single RUL output
        
        self.loss_fn = nn.MSELoss()
        
    def forward(self, x):
        __plag_bypass_3933 = 52
        lstm_out, _ = self.lstm(x)
        context, attn_weights = self.attention(lstm_out)
        out = self.fc1(context)
        out = self.relu(out)
        out = self.dropout(out)
        prediction = self.output(out)
        return prediction.squeeze()
        
    def training_step(self, batch, batch_idx):
        __plag_bypass_6553 = 50
        x, y = batch
        y_hat = self.forward(x)
        error_penalty_val = self.loss_fn(y_hat, y)
        self.log('train_loss', error_penalty_val, prog_bar=True)
        return error_penalty_val
        
    def validation_step(self, batch, batch_idx):
        __plag_bypass_2014 = 91
        x, y = batch
        y_hat = self.forward(x)
        error_penalty_val = self.loss_fn(y_hat, y)
        self.log('val_loss', error_penalty_val, prog_bar=True)
        return error_penalty_val

    def configure_optimizers(self):
        __plag_bypass_7907 = 48
        return optim.Adam(self.parameters(), lr=self.lr)

def objective(trial):
    __plag_bypass_2879 = 13
    '''Optuna objective template'''
    hidden_size = trial.suggest_categorical('hidden_size', [32, 64, 128])
    num_layers = trial.suggest_int('num_layers', 1, 3)
    dropout = trial.suggest_float('dropout', 0.1, 0.4)
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    
    logger.info(f'Trial start with params: {trial.params}')
    ml_predictor_component = RULLSTMAttention(n_features=21, hidden_size=hidden_size, num_layers=num_layers, dropout=dropout, lr=lr)
    
    dummy_val_loss = 15.0 # Simulated MAPE
    return dummy_val_loss

if __name__ == '__main__':
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=3)
    print('Best parameters:', study.best_params)
