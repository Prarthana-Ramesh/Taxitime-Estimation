# # e.g., sklearn RandomForest
# from sklearn.ensemble import RandomForestRegressor
# rf = RandomForestRegressor(n_estimators=200)
# X = np.vstack([d.global_feat.numpy().ravel() for d in dataset_list])
# y = np.array([d.y.item() for d in dataset_list])
# # split & train ...

# baseline.py
import torch
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

def extract_global_matrix(dataset_list):
    """
    dataset_list: list of PyG Data objects (data.global_feat is scaled later)
    returns X (N x 3), y (N,)
    """
    X = []
    y = []
    for d in dataset_list:
        gf = d.global_feat.numpy().ravel()
        X.append(gf)
        y.append(float(d.y.item()))
    X = np.vstack(X)
    y = np.array(y, dtype=float)
    return X, y

def train_baseline(dataset_list, save_path='processed/baseline_rf.joblib'):
    X, y = extract_global_matrix(dataset_list)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    preds = rf.predict(X_val)
    mae = mean_absolute_error(y_val, preds)
    mse = mean_squared_error(y_val, preds)
    rmse = mse ** 0.5
    print(f"Baseline RF val MAE={mae:.2f}s RMSE={rmse:.2f}s")
    joblib.dump(rf, save_path)
    print(f"Saved baseline model to {save_path}")
    return rf, mae, rmse

def load_baseline(path='processed/baseline_rf.joblib'):
    return joblib.load(path)

if __name__ == "__main__":
    import sys
    # quick entry when processed dataset exists
    ds_path = 'processed/dataset_list.pt'
    ds = torch.load(ds_path, weights_only=False)
    train_baseline(ds)

