import os
import glob
import pandas as pd
import numpy as np
import torch
from tqdm import tqdm
from datetime import datetime

from utilities import haversine_m
from input_processor import path_to_pyg_data

NEAREST_VERTEX_THRESHOLD_M = 30.0
MIN_POINTS_PER_SEGMENT = 3
TIME_COLS = ['Timestamp','UTC']

def load_taxiway_vertices(vertex_file_path):
    """
    Loads Taxiway_Vertex_Data (xlsx or csv)
    Expected columns:
        Vertex_Index | Latitude | Longitude
    Returns:
        vertex_index_to_coords = {vertex_index: (lat, lon)}
    """
    # Auto-detect file format (xlsx or csv)
    if vertex_file_path.lower().endswith('.csv'):
        df = pd.read_csv(vertex_file_path)
    else:
        df = pd.read_excel(vertex_file_path)
    df = df.rename(columns={c: c.strip() for c in df.columns})

    # detect columns dynamically
    idx_col = next((c for c in df.columns if "vertex" in c.lower()), None)
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower()), None)

    if idx_col is None or lat_col is None or lon_col is None:
        raise ValueError("Could not find Vertex_Index / Latitude / Longitude columns in Vertex file.")

    vertex_index_to_coords = {}
    for _, r in df.iterrows():
        vid = int(r[idx_col])
        lat = float(r[lat_col])
        lon = float(r[lon_col])
        vertex_index_to_coords[vid] = (lat, lon)

    return vertex_index_to_coords



def load_taxiway_segments(twy_file_path):
    """
    Loads KTEB_Taxiway_Data (xlsx or csv)
    Expected columns:
        Ident | Vertex_Count | Vertex_Indices
    Vertex_Indices may contain: "1,2,3,4" OR "1;2;3;4"
    """
    # Auto-detect file format (xlsx or csv)
    if twy_file_path.lower().endswith('.csv'):
        df = pd.read_csv(twy_file_path, dtype=str).fillna('')
    else:
        df = pd.read_excel(twy_file_path, dtype=str).fillna('')
    df = df.rename(columns={c: c.strip() for c in df.columns})

    ident_col = next((c for c in df.columns if "ident" in c.lower()), None)
    vinds_col = next((c for c in df.columns if "vertex" in c.lower()), None)

    if ident_col is None or vinds_col is None:
        raise ValueError("Could not find Ident / Vertex_Indices columns in Taxiway file.")

    segs = []
    for _, r in df.iterrows():
        ident = str(r[ident_col]).strip()
        v_raw = str(r[vinds_col]).strip()

        if ";" in v_raw:
            raw_list = [x.strip() for x in v_raw.split(";") if x.strip()]
        elif "," in v_raw:
            raw_list = [x.strip() for x in v_raw.split(",") if x.strip()]
        else:
            raw_list = [x.strip() for x in v_raw.split() if x.strip()]

        try:
            vinds = [int(v) for v in raw_list]
        except:
            vinds = []

        if vinds:
            segs.append((ident, vinds))

    return segs

def read_flight_csv(path):
    """
    Reads flight CSV → normalizes columns.
    Expected columns:
       Timestamp | UTC | Callsign | Position | Altitude | Speed | Direction
    """
    df = pd.read_csv(path)
    df = df.rename(columns={c: c.strip() for c in df.columns})

    if "UTC" in df.columns:
        df['__ts'] = pd.to_datetime(df["UTC"], errors='coerce', utc=True)
    else:
        ts = df[df.columns[0]].astype(str)
        mask_sec = ts.str.match(r"^\d{10}$")
        mask_ms  = ts.str.match(r"^\d{13}$")

        df['__ts'] = pd.NaT

        if mask_sec.any():
            df.loc[mask_sec, '__ts'] = pd.to_datetime(ts[mask_sec].astype(int), unit='s', errors='coerce')

        if mask_ms.any():
            df.loc[mask_ms, '__ts'] = pd.to_datetime(ts[mask_ms].astype(int), unit='ms', errors='coerce')

        mask_normal = df['__ts'].isna()
        df.loc[mask_normal, '__ts'] = pd.to_datetime(ts[mask_normal], errors='coerce')


    if 'Position' in df.columns:
        split_pos = df['Position'].astype(str).str.split(",", expand=True)
        if split_pos.shape[1] >= 2:
            df['latitude'] = pd.to_numeric(split_pos[0], errors='coerce')
            df['longitude'] = pd.to_numeric(split_pos[1], errors='coerce')
    else:
        latc = next((c for c in df.columns if "lat" in c.lower()), None)
        lonc = next((c for c in df.columns if "lon" in c.lower()), None)
        df['latitude'] = pd.to_numeric(df.get(latc), errors='coerce')
        df['longitude'] = pd.to_numeric(df.get(lonc), errors='coerce')

    altc = next((c for c in df.columns if "alt" in c.lower()), "Altitude")
    df['altitude'] = pd.to_numeric(df.get(altc, 0), errors='coerce').fillna(0)

    callc = next((c for c in df.columns if "call" in c.lower()), None)
    df['callsign'] = df.get(callc, df.get("Callsign", "UNKNOWN")).astype(str)

    return df



def extract_zero_altitude_segments(df):
    """
    Finds continuous taxi segments (altitude = 0).
    Returns list of:
        {
            'start_ts', 'end_ts', 'lats': [], 'lons': []
        }
    """
    df = df.sort_values('__ts').reset_index(drop=True)

    mask = (df['altitude'] == 0)
    df['zero_mask'] = mask.astype(int)
    df['run_id'] = (df['zero_mask'] != df['zero_mask'].shift(1)).cumsum()

    segments = []
    for run_id, seg in df.groupby('run_id'):
        if seg['zero_mask'].iloc[0] != 1:
            continue
        if len(seg) < MIN_POINTS_PER_SEGMENT:
            continue

        segments.append({
            'start_ts': seg['__ts'].iloc[0],
            'end_ts': seg['__ts'].iloc[-1],
            'lats': seg['latitude'].tolist(),
            'lons': seg['longitude'].tolist(),
        })

    return segments



def build_vertex_arrays(vertex_index_to_coords):
    """
    Converts vertex dict → numpy arrays for fast nearest search.
    """
    vids = np.array(list(vertex_index_to_coords.keys()))
    lats = np.array([vertex_index_to_coords[v][0] for v in vids])
    lons = np.array([vertex_index_to_coords[v][1] for v in vids])
    return vids, lats, lons



def find_nearest_vertex(lat, lon, vids, lat_arr, lon_arr):
    """
    Simple vectorized haversine distance to all vertices → pick min.
    """
    lat_rad = np.radians(lat)
    phi1 = np.radians(lat_arr)
    dphi = np.radians(lat_arr - lat)
    dlon = np.radians(lon_arr - lon)

    a = np.sin(dphi/2)**2 + np.cos(lat_rad)*np.cos(phi1)*(np.sin(dlon/2)**2)
    c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))
    d = 6371000.0*c

    idx = np.argmin(d)
    return vids[idx], float(d[idx])



def map_match_segment(seg, vids, lat_arr, lon_arr):
    """
    Converts GPS points → nearest taxiway vertices.
    """
    mapped = []

    for lat, lon in zip(seg['lats'], seg['lons']):
        if pd.isna(lat) or pd.isna(lon):
            continue
        vid, dist = find_nearest_vertex(lat, lon, vids, lat_arr, lon_arr)
        if dist <= NEAREST_VERTEX_THRESHOLD_M:
            mapped.append(vid)

    if not mapped:
        return []

    final_path = [mapped[0]]
    for v in mapped[1:]:
        if v != final_path[-1]:
            final_path.append(v)

    return final_path

def create_dataset_from_raw(
        taxiway_vertex_xlsx,
        taxiway_data_xlsx,
        takeoff_dir,
        landing_dir,
        out_dataset="processed/dataset_list.pt",
        out_vertexmap="processed/vertex_index_to_coords.pt"
    ):
    """
    Reads all .xlsx & .csv → produces dataset_list.pt of PyG Data objects.
    """

    vertex_index_to_coords = load_taxiway_vertices(taxiway_vertex_xlsx)
    segments = load_taxiway_segments(taxiway_data_xlsx)
    vids, lat_arr, lon_arr = build_vertex_arrays(vertex_index_to_coords)

    files = glob.glob(os.path.join(takeoff_dir, "*.csv")) + \
            glob.glob(os.path.join(landing_dir, "*.csv"))

    dataset_list = []

    for fp in tqdm(files, desc="Processing flight logs"):
        try:
            df = read_flight_csv(fp)
        except Exception as e:
            print("Skipping file:", fp, e)
            continue

        taxi_segments = extract_zero_altitude_segments(df)

        for seg in taxi_segments:
            vertex_path = map_match_segment(seg, vids, lat_arr, lon_arr)

            if len(vertex_path) < 2:
                continue

            taxi_time_seconds = (seg['end_ts'] - seg['start_ts']).total_seconds()
            if taxi_time_seconds <= 0:
                continue

            try:
                data = path_to_pyg_data(
                    vertex_path,
                    vertex_index_to_coords,
                    taxi_time_seconds
                )
                dataset_list.append(data)
            except Exception as e:
                print("Skipped a segment (path_to_pyg_data error):", e)
                continue

    os.makedirs("processed", exist_ok=True)
    torch.save(dataset_list, out_dataset)
    torch.save(vertex_index_to_coords, out_vertexmap)

    print(f"\nSaved {len(dataset_list)} training examples:")
    print(f"  → {out_dataset}")
    print(f"  → {out_vertexmap}")

    return dataset_list, vertex_index_to_coords
