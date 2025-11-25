# train.py
import torch
import numpy as np
import torch.optim as optim
from torch_geometric.data import DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from gnn import TaxiTimeGNN
import os

# path to processed dataset (created by data_processor.create_dataset_from_raw)
PROCESSED_DATASET_PATH = 'processed/dataset_list.pt'
SCALER_SAVE_PATH = 'processed/global_feat_scaler.npy'  # we'll save mean/std

def collate_and_normalize(dataset):
    # Fit scaler on all global features (shape [1,3] per data)
    import numpy as np
    globals_all = np.vstack([d.global_feat.numpy().ravel() for d in dataset])
    scaler = StandardScaler()
    scaler.fit(globals_all)
    for d in dataset:
        d.global_feat = torch.tensor(scaler.transform(d.global_feat.numpy()), dtype=torch.float)
    # save scaler params
    np.save(SCALER_SAVE_PATH, {'mean': scaler.mean_, 'scale': scaler.scale_}, allow_pickle=True)
    return dataset, scaler

def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0
    for data in loader:
        data = data.to(device)
        optimizer.zero_grad()
        pred = model(data)
        loss = torch.nn.functional.mse_loss(pred, data.y.view(-1).to(pred.dtype))
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * data.num_graphs
    return total_loss / len(loader.dataset)

def evaluate(model, loader, device):
    model.eval()
    ys, preds = [], []
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            pred = model(data).cpu().numpy()
            y = data.y.cpu().numpy().reshape(-1)
            preds.append(pred)
            ys.append(y)
    preds = np.concatenate(preds)
    ys = np.concatenate(ys)
    mae = mean_absolute_error(ys, preds)
    rmse = np.sqrt(mean_squared_error(ys, preds))
    return mae, rmse, ys, preds

def load_dataset(processed_path=PROCESSED_DATASET_PATH):
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Processed dataset not found at {processed_path}. Run data_processor.create_dataset_from_raw first.")
    dataset_list = torch.load(processed_path, weights_only=False)
    return dataset_list

def train_main(num_epochs=65, batch_size=32, lr=1e-3, device=None):
    device = device or (torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
    dataset_list = load_dataset()
    dataset_list, scaler = collate_and_normalize(dataset_list)
    np.random.seed(42)
    np.random.shuffle(dataset_list)
    split = int(0.8 * len(dataset_list))
    train_ds = dataset_list[:split]
    val_ds = dataset_list[split:]
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = TaxiTimeGNN(node_in=2).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    for epoch in range(1, num_epochs + 1):
        tr_loss = train_epoch(model, train_loader, optimizer, device)
        val_mae, val_rmse, _, _ = evaluate(model, val_loader, device)
        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch} train_loss={tr_loss:.4f}, val_mae={val_mae:.2f}s, val_rmse={val_rmse:.2f}s")

    # save model
    os.makedirs('processed', exist_ok=True)
    torch.save(model.state_dict(), 'processed/gnn_model.pt')
    print("Saved GNN weights to processed/gnn_model.pt")
    return model, scaler

# ---- simple evaluation helper for single-path inference ----
from utilities import haversine_m
import numpy as np
def predict_for_vertex_path(model, vertex_path, vertex_index_to_coords, scaler=None, device=None):
    """
    vertex_path: list of vertex indices (in correct order)
    vertex_index_to_coords: dict {vertex_index: (lat,lon)}
    scaler: fitted StandardScaler (if None, will attempt to load SCALER_SAVE_PATH)
    """
    device = device or (torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
    # reuse input_processor.path_to_pyg_data
    from input_processor import path_to_pyg_data
    data = path_to_pyg_data(vertex_path, vertex_index_to_coords, target_taxi_time_seconds=0.0)
    if scaler is None:
        if os.path.exists(SCALER_SAVE_PATH):
            obj = np.load(SCALER_SAVE_PATH, allow_pickle=True).item()
            mean = obj['mean']; scale = obj['scale']
            data.global_feat = torch.tensor((data.global_feat.numpy() - mean) / scale, dtype=torch.float)
        else:
            print("Warning: scaler not provided and saved scaler not found. Using raw global features (may be wrong).")
    else:
        data.global_feat = torch.tensor(scaler.transform(data.global_feat.numpy()), dtype=torch.float)
    data.batch = torch.zeros(data.x.size(0), dtype=torch.long)
    model = model.to(device)
    model.eval()
    data = data.to(device)
    with torch.no_grad():
        pred = model(data).cpu().numpy()
    return float(pred[0])

if __name__ == "__main__":
    # quick train when running this script
    train_main()
