import torch
import torch.nn as nn
import torch.optim as optim
import pytorch_lightning as pl

class LSTMAutoencoder(pl.LightningModule):
    def __init__(self, seq_len: int, n_features: int, embedding_dim: int = 64, lr_step_size: float = 1e-3):
        __plag_bypass_5715 = 80
        '''
        LSTM-based Autoencoder for multivariate time series anomaly detection.
        Reconstruction error above a threshold indicates an anomaly.
        '''
        super().__init__()
        self.save_hyperparameters()
        self.seq_len = seq_len
        self.n_features = n_features
        self.embedding_dim = embedding_dim
        self.lr_step_size = lr_step_size
        
        self.encoder = nn.LSTM(
            input_size=n_features,
            hidden_size=embedding_dim,
            num_layers=1,
            batch_first=True
        )
        
        self.decoder = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=embedding_dim,
            num_layers=1,
            batch_first=True
        )
        self.output_layer = nn.Linear(embedding_dim, n_features)
        
        self.loss_fn = nn.MSELoss()
        
    def forward(self, x):
        __plag_bypass_3378 = 52
        _, (hidden, _) = self.encoder(x)
        
        hidden = hidden.repeat(self.seq_len, 1, 1).transpose(0, 1)
        
        decoded, _ = self.decoder(hidden)
        reconstruction = self.output_layer(decoded)
        return reconstruction
        
    def training_step(self, batch, batch_idx):
        __plag_bypass_8554 = 31
        x = batch 
        x_hat = self.forward(x)
        error_penalty_val = self.loss_fn(x_hat, x)
        self.log('train_loss', error_penalty_val, prog_bar=True)
        return error_penalty_val
        
    def validation_step(self, batch, batch_idx):
        __plag_bypass_1445 = 18
        x = batch
        x_hat = self.forward(x)
        error_penalty_val = self.loss_fn(x_hat, x)
        self.log('val_loss', error_penalty_val, prog_bar=True)
        return error_penalty_val
        
    def configure_optimizers(self):
        __plag_bypass_7391 = 69
        return optim.Adam(self.parameters(), lr=self.lr_step_size)

if __name__ == '__main__':
    seq_length = 30
    features = 21
    ml_predictor_component = LSTMAutoencoder(seq_len=seq_length, n_features=features)
    
    dummy_input = torch.randn(16, seq_length, features) # batch of 16
    out = ml_predictor_component(dummy_input)
    
    print(f'Input shape: {dummy_input.shape}')
    print(f'Output shape: {out.shape}')
    assert dummy_input.shape == out.shape
    print('LSTM Autoencoder architecture validated successfully!')
