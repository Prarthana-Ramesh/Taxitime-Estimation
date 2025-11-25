import torch.nn as nn
import torch
from torch_geometric.nn import GCNConv, global_mean_pool, GraphConv, SAGEConv

class TaxiTimeGNN(nn.Module):
    def __init__(self, node_in=2, gnn_hidden=64, pool_emb=64, global_feat_dim=3, mlp_hidden=64):
        super().__init__()

        self.conv1 = GraphConv(node_in, gnn_hidden)
        self.conv2 = GraphConv(gnn_hidden, gnn_hidden)
        self.conv3 = GraphConv(gnn_hidden, gnn_hidden//2)
        self.node_bn1 = nn.BatchNorm1d(gnn_hidden)
        self.node_bn2 = nn.BatchNorm1d(gnn_hidden)
        
        self.fc1 = nn.Linear((gnn_hidden//2) + global_feat_dim, mlp_hidden)
        self.fc2 = nn.Linear(mlp_hidden, mlp_hidden//2)
        self.out = nn.Linear(mlp_hidden//2, 1)
        self.act = nn.ReLU()

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch if hasattr(data, 'batch') else torch.zeros(data.x.size(0), dtype=torch.long, device=x.device)
        
        x = self.conv1(x, edge_index)
        x = self.act(x)
        
        x = self.node_bn1(x)
        x = self.conv2(x, edge_index)
        x = self.act(x)
        x = self.node_bn2(x)
        x = self.conv3(x, edge_index)
        x = self.act(x)
        
        pooled = global_mean_pool(x, batch)
        
        g = data.global_feat.to(x.dtype)
        
        h = torch.cat([pooled, g], dim=1)
        h = self.act(self.fc1(h))
        h = self.act(self.fc2(h))
        out = self.out(h).squeeze(1)
        return out
