import os
import torch
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

from baseline import load_baseline
from gnn import TaxiTimeGNN

from data_processor import (
    load_taxiway_vertices,
    read_flight_csv,
    extract_zero_altitude_segments,
    build_vertex_arrays,
    map_match_segment,
)
from input_processor import path_to_pyg_data

TAXIWAY_VERTEX_FILE = "data_raw/Taxiway_Vertex_Data.xlsx"

EVAL_TAKEOFF_DIR = "data_raw/takeoffs"
EVAL_LANDING_DIR = "data_raw/landings"

GNN_MODEL_PATH      = "processed/gnn_model.pt"
BASELINE_MODEL_PATH = "processed/baseline_rf.joblib"
SCALER_PATH         = "processed/global_feat_scaler.npy"

def load_scaler():
    obj = np.load(SCALER_PATH, allow_pickle=True).item()
    return obj["mean"], obj["scale"]

def build_eval_dataset():
    print("Loading taxiway vertices...")
    vertex_map = load_taxiway_vertices(TAXIWAY_VERTEX_FILE)
    vids, lat_arr, lon_arr = build_vertex_arrays(vertex_map)

    files  = [os.path.join(EVAL_TAKEOFF_DIR, f)  for f in os.listdir(EVAL_TAKEOFF_DIR)  if f.lower().endswith(".csv")]
    files += [os.path.join(EVAL_LANDING_DIR, f) for f in os.listdir(EVAL_LANDING_DIR) if f.lower().endswith(".csv")]

    print(f"Found {len(files)} evaluation files.")

    dataset = []

    for fp in files:
        print(f"\n=== Processing {os.path.basename(fp)} ===")

        try:
            df = read_flight_csv(fp)
        except:
            print("Could not read file, skipping.")
            continue

        df["altitude"] = df["altitude"].fillna(0).astype(float)
        df["altitude_flag"] = (df["altitude"] == 0)

        segments = extract_zero_altitude_segments(df)
        print(f"  Ground segments: {len(segments)}")

        for seg_index, seg in enumerate(segments):
            print(f"   Segment {seg_index}: first_ts = {seg['start_ts']}, last_ts = {seg['end_ts']}")

            taxi_time = (seg["end_ts"] - seg["start_ts"]).total_seconds()
            print(f"      Raw taxi time = {taxi_time} seconds")

            vertex_path = map_match_segment(seg, vids, lat_arr, lon_arr)
            print(f"      Matched vertices: {len(vertex_path)}")

            if len(vertex_path) < 2:
                print("      Dropped: <2 vertices")
                continue

            if taxi_time <= 0:
                print("      Dropped: negative or zero taxi time")
                continue

            print("      ACCEPTED SEGMENT")
            data = path_to_pyg_data(vertex_path, vertex_map, taxi_time)
            dataset.append(data)

    print(f"\nTotal evaluation samples: {len(dataset)}")
    return dataset, vertex_map


def scale_dataset(dataset, mean, scale):
    for d in dataset:
        d.global_feat = torch.tensor((d.global_feat.numpy() - mean) / scale, dtype=torch.float)
    return dataset

def evaluate_baseline(dataset):
    print("\nEvaluating baseline model...")

    model = load_baseline(BASELINE_MODEL_PATH)

    X = np.vstack([d.global_feat.numpy().ravel() for d in dataset])
    y = np.array([float(d.y.item()) for d in dataset])

    preds = model.predict(X)

    mae = mean_absolute_error(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))

    print(f"Baseline MAE:  {mae:.2f} sec")
    print(f"Baseline RMSE: {rmse:.2f} sec")
    return mae, rmse

def evaluate_gnn(dataset):
    print("\nEvaluating GNN model...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = TaxiTimeGNN()
    model.load_state_dict(torch.load(GNN_MODEL_PATH, weights_only=False))
    model.to(device)
    model.eval()

    ys, preds = [], []

    for d in dataset:
        d.batch = torch.zeros(len(d.x), dtype=torch.long)
        d = d.to(device)

        with torch.no_grad():
            p = model(d).cpu().numpy()[0]

        preds.append(p)
        ys.append(float(d.y.item()))

    ys = np.array(ys)
    preds = np.array(preds)

    mae = mean_absolute_error(ys, preds)
    rmse = np.sqrt(mean_squared_error(ys, preds))

    print(f"GNN MAE:  {mae:.2f} sec")
    print(f"GNN RMSE: {rmse:.2f} sec")
    return mae, rmse


if __name__ == "__main__":
    eval_dataset, vertex_map = build_eval_dataset()

    if len(eval_dataset) == 0:
        print("\nNo evaluation samples found.")
        exit()

    mean, scale = load_scaler()
    eval_dataset = scale_dataset(eval_dataset, mean, scale)

    evaluate_baseline(eval_dataset)
    evaluate_gnn(eval_dataset)
