import torch
import torch.nn as nn


class SignTransformer(nn.Module):

    def __init__(self, input_dim, num_classes):

        super().__init__()

        self.embedding = nn.Linear(input_dim, 256)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=256,
            nhead=8,
            dim_feedforward=512,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=4
        )

        self.fc = nn.Linear(256, num_classes)


    def forward(self, x):

        x = self.embedding(x)

        x = self.transformer(x)

        x = x.mean(dim=1)

        return self.fc(x)
    
    #FOR BEAST MODEL