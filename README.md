# Taxi Time Prediction Using Graph Neural Networks

## Overview
This project develops a machine learning pipeline to estimate aircraft taxi times at Teterboro Airport (KTEB). Taxi time prediction is essential for improving airport surface efficiency, reducing delays, and enabling better planning for airside resource usage.

We implement and compare three modeling approaches:
1. A Graph Neural Network (GNN) using taxiway geometry.
2. A Random Forest regression baseline.
3. A statistical baseline using historical averages.

The project includes full data preprocessing, map matching, model training, and evaluation.

---

## 1. Progress So Far

### 1.1 Model Development
We built a Graph Neural Network that predicts taxi time using minimal geometric features:
- Path length (meters)
- Number of turns
- Average turn sharpness

Node-level features:
- Latitude
- Longitude

This lightweight feature set helps confirm the correctness of the graph structure and data pipeline before adding complex operational features.

### 1.2 Data Preprocessing and Map Matching
A robust preprocessing pipeline is implemented, which includes:
- Parsing takeoff and landing flight logs
- Cleaning and normalizing timestamp and position fields
- Using UTC timestamps as the authoritative time source
- Filtering altitude-0 rows to only include points physically located near KTEB
- Splitting the data into continuous ground segments
- Map-matching each GPS point to the nearest taxiway vertex (no distance threshold)
- Constructing graph objects suitable for PyTorch Geometric

Datasets used:
- `Taxiway_Vertex_Data.xlsx`: Contains coordinates for all taxiway vertices.
- `KTEB_Taxiway_Data.xlsx`: Contains taxiway segments and vertex sequences.
- Multiple takeoff and landing ADS-B CSV files.

### 1.3 Baseline Models
Two baselines were implemented:
- **Random Forest Regression** using the same global features as the GNN.
- **Statistical Model** computing historical average taxi time for each route.

### 1.4 Current Results
baseline model
- Baseline MAE: 321.82 sec
- Baseline RMSE: 423.38 sec

GNN model
- GNN MAE: 237.22 sec
- GNN RMSE: 331.88 sec
---

## 2. Observations

1. The GNN outperforms the Random Forest baseline.
2. Overall error remains high due to limited dataset size, noisy ADS-B logs, and the minimal feature set.
3. The current results indicate that additional features and richer path representations are needed for meaningful accuracy improvements.

---

## 3. Next Tasks and Roadmap

### 3.1 Parsing Taxiway Route Strings
Add functionality to parse routes in the format:RW27-C3-C-F5-F
Tasks include:
- Mapping identifiers to vertex sequences
- Building graph representations for these routes
- Supporting inference on user-defined taxi paths in the frontend

### 3.2 Increasing Dataset Volume
Current training data is limited. The plan is to:
- Scrape additional takeoff and landing logs
- Expand the diversity of taxi observations
- Improve generalization through greater data coverage

### 3.3 Adding Aircraft-Level Features
Once sufficient data is available, incorporate:
- Aircraft type / ICAO code
- Engine class and weight classification
- Performance characteristics

### 3.4 Future Feature Engineering
Future improvements may include:
- Weather variables (wind, precipitation, temperature)
- Surface congestion information
- Hotspot and bottleneck features
- Time-of-day and operational context

---

## 4. Training Pipeline

### Generate Training Dataset
python -c "from data_processor import create_dataset_from_raw; create_dataset_from_raw('data_raw/Taxiway_Vertex_Data.xlsx','data_raw/KTEB_Taxiway_Data.xlsx','data_raw/takeoffs','data_raw/landings')"


### Train Models


python train.py
python baseline.py


### Evaluate Models


python evaluate.py


---

## 5. Frontend Setup

### Create a Next.js Frontend (TypeScript + Tailwind)


npx create-next-app@latest frontend --typescript --tailwind --eslint


### Build


npm run build


### Development Server


npm run dev



