#!/usr/bin/env python
"""
Script to organize data files into the expected structure:
  Taxitime-Estimation/
    ├── data_raw/
    │   ├── takeoffs/       (copy all takeoff CSVs here)
    │   ├── landings/       (copy all landing CSVs here)
    │   ├── KTEB_Taxiway_Data.csv
    │   └── Taxiway_Vertex_Data.csv (if exists)
"""

import os
import shutil
import glob

# Define paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Parent of scripts/
data_raw_dir = os.path.join(project_root, "data_raw")
takeoffs_dir = os.path.join(data_raw_dir, "takeoffs")
landings_dir = os.path.join(data_raw_dir, "landings")

# Paths to source data
parent_root = os.path.dirname(project_root)  # honeyWell folder
flight_data_root = os.path.join(parent_root, "KTEB_Flight_Data (1)", "KTEB_Flight_Data")
taxiway_csv = os.path.join(parent_root, "KTEB_Taxiway_Data.csv")

# Create directories
os.makedirs(takeoffs_dir, exist_ok=True)
os.makedirs(landings_dir, exist_ok=True)
print(f"✓ Created directories: {data_raw_dir}")

# Copy takeoff CSVs
takeoff_source = os.path.join(flight_data_root, "Takeoff")
if os.path.exists(takeoff_source):
    takeoff_csvs = glob.glob(os.path.join(takeoff_source, "*.csv"))
    for src in takeoff_csvs:
        dst = os.path.join(takeoffs_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        print(f"✓ Copied: {os.path.basename(src)} → takeoffs/")
    print(f"  Total takeoff CSVs copied: {len(takeoff_csvs)}")
else:
    print(f"⚠ Takeoff source not found: {takeoff_source}")

# Copy landing CSVs
landing_source = os.path.join(flight_data_root, "Landing")
if os.path.exists(landing_source):
    landing_csvs = glob.glob(os.path.join(landing_source, "*.csv"))
    for src in landing_csvs:
        dst = os.path.join(landings_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        print(f"✓ Copied: {os.path.basename(src)} → landings/")
    print(f"  Total landing CSVs copied: {len(landing_csvs)}")
else:
    print(f"⚠ Landing source not found: {landing_source}")

# Copy taxiway CSV
if os.path.exists(taxiway_csv):
    dst_taxiway = os.path.join(data_raw_dir, "KTEB_Taxiway_Data.csv")
    shutil.copy2(taxiway_csv, dst_taxiway)
    print(f"✓ Copied: KTEB_Taxiway_Data.csv → data_raw/")
else:
    print(f"⚠ Taxiway CSV not found: {taxiway_csv}")

print("\n" + "="*60)
print("Data organization complete!")
print(f"Structure created at: {data_raw_dir}/")
print("="*60)
