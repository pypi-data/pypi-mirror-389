import torch
import torch.nn as nn
import os

import torch
import torch.nn as nn

class Inverse_Net(nn.Module):
    def __init__(
        self,
        layer_dims=[2001, 6],  # user-defined layer structure
        use_attention=True,
        dropout_rate=0.5
    ):
        """
        Parameters
        ----------
        layer_dims : list[int]
            Example: [2001, 100, 10] means input 2001-D → hidden 100-D → output 10-D.
        use_attention : bool
            Whether to enable the attention-based multi-head mode.
        dropout_rate : float
            Dropout rate used for non-attention MLP layers.
        """
        super(Inverse_Net, self).__init__()

        self.use_attention = use_attention
        self.heads = heads = layer_dims[-1]
        self.flatten = nn.Flatten()

        # ---------- Mode 1: Multi-head attention ----------
        if use_attention:
            # Adjust dimensions for attention mode
            layer_dims[-1] = 1
            layer_dims.insert(0, layer_dims[0])

            input_size = layer_dims[0]
            hidden_size = layer_dims[1] if len(layer_dims) > 1 else input_size
            output_size = layer_dims[-1]

            # Attention layers (one per head)
            self.attention_layers = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(input_size, hidden_size, bias=False),
                    nn.Sigmoid()
                ) for _ in range(heads)
            ])

            # Output layers for each head
            self.end_layers = nn.ModuleList([
                nn.Sequential(
                    nn.Linear(hidden_size, output_size),
                    nn.Sigmoid()
                ) for _ in range(heads)
            ])

            # Final fusion layer for combining multi-head outputs
            self.final_layer = nn.Sequential(
                nn.Linear(heads, heads),
                nn.Sigmoid()
            )

        # ---------- Mode 2: Standard MLP ----------
        else:
            layers = []
            for i in range(len(layer_dims) - 1):
                layers.append(nn.Linear(layer_dims[i], layer_dims[i + 1]))
                # Add activation and dropout for hidden layers only
                if i < len(layer_dims) - 2:
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(p=dropout_rate))

            self.mlp = nn.Sequential(*layers)

    def forward(self, x):
        # ---------- Mode 1: Multi-head attention ----------
        if self.use_attention:
            outputs = []
            for i in range(self.heads):
                # Compute attention weights for each head
                attention_weights = self.attention_layers[i](x)
                weighted_x = torch.multiply(attention_weights, x)

                # Pass through the head-specific output layer
                output = self.end_layers[i](weighted_x)
                outputs.append(output)

            print(output.shape)

            # Concatenate all head outputs
            concatenated_output = self.flatten(torch.cat(outputs, dim=1))
            print(concatenated_output.shape)

            # Compute final attention weights and apply them
            final_attention_weights = self.final_layer(concatenated_output)
            final_output = torch.multiply(final_attention_weights, concatenated_output)
            return final_output

        # ---------- Mode 2: Standard MLP ----------
        else:
            return self.mlp(x)


def load_encoder(weights_path=None, device="cpu"):
    if weights_path is None:
        # 自动获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        weights_path = os.path.join(current_dir, "weights", "peng_2025_weights.pt")
        print(weights_path)
    model = fast_ann(layer_dims=[2001, 2001, 6], use_attention=True)
    state_dict = torch.load(weights_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    return model