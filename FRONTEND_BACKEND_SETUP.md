# Frontend-Backend Integration Complete ✅

## Overview
Your Taxi-Time Estimation system is now fully integrated and running with:
- **Backend API**: Flask server on `http://localhost:5000`
- **Frontend**: Next.js web app on `http://localhost:3000`

---

## What's Running

### Backend (Flask)
- **Status**: ✅ Running on port 5000
- **Location**: `/Taxitime-Estimation/app.py`
- **Features**:
  - Loads trained GNN and Random Forest models
  - Builds airport taxiway graph
  - Provides REST API endpoints for predictions

### Frontend (Next.js)
- **Status**: ✅ Running on port 3000
- **Location**: `/Taxitime-Estimation/frontend/`
- **Features**:
  - Beautiful blueprint-themed UI
  - Three model prediction cards (GNN, Random Forest, Statistical Mean)
  - Real-time API communication with backend
  - Live path statistics display
  - Backend health check indicator

---

## API Endpoints

### 1. Health Check
```
GET /api/health
```
Returns: `{ "status": "ok", "models_loaded": true }`

### 2. Predict Taxi Time
```
POST /api/predict
Content-Type: application/json

{
  "route": "RW27-C3-C-F5-F",
  "model": "ensemble"  // or "gnn", "rf"
}
```

Response:
```json
{
  "success": true,
  "route": "RW27-C3-C-F5-F",
  "normalized_route": "C → F",
  "predictions": {
    "gnn": 47.0,
    "rf": 67.1,
    "ensemble": 57.0
  },
  "path_stats": {
    "path_length_m": 1234.5,
    "path_length_ft": 4052,
    "num_turns": 2,
    "sharpness": 45.3
  }
}
```

### 3. Available Taxiways
```
GET /api/taxiways
```
Returns: List of all available taxiway identifiers at KTEB

### 4. Example Routes
```
GET /api/example-routes
```
Returns: Sample routes for testing

---

## How to Use

### From Frontend (Recommended)
1. Open `http://localhost:3000` in your browser
2. Enter a taxiway route in any of the three model cards:
   - Examples: `L-C-H`, `RW27-C3-C-F5-F`, `A-B-C`
3. Click "Estimate Taxi Time"
4. View predictions from each model and combined statistics

### From Command Line
```powershell
# Single prediction
C:\...\python.exe predict.py --route "RW27-C3-C-F5-F"

# List all taxiways
C:\...\python.exe predict.py --list
```

### From API (cURL)
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"route":"L-C-H","model":"ensemble"}'
```

---

## Route Format Support

The system accepts routes in multiple formats:

- **Single taxiway**: `L`, `C`, `H`
- **Hyphen-separated**: `L-C-H-F`, `RW27-C3-C-F5-F`
- **Comma-separated**: `L,C,H,F`, `A,B,C`
- **Mixed formats**: `RW27-C3-C-F5-F` (runway designators automatically normalized)

The parser intelligently:
- Strips runway prefixes (RW27 → ignored)
- Extracts letters from numbered connectors (C3 → C, F5 → F)
- Deduplicates consecutive segments
- Validates against database

---

## Files Modified/Created

### New Files
- **`app.py`** - Flask backend API server
  - Loads models and airport graph
  - Provides REST endpoints
  - Returns predictions with path statistics
  - Integrates with predict.py

### Modified Files
- **`predict.py`** - Enhanced prediction logic
  - New parameters: `route`, `route_string`, `models`, `airport_graph`
  - Returns dict instead of just printing
  - Supports `return_path_stats` parameter
  - Optional verbose mode
  - Backward compatible with CLI

- **`frontend/components/taxi-time-estimator.tsx`** - Updated React component
  - Connects to backend API via HTTP
  - Displays real predictions (no mock data)
  - Shows backend connection status
  - Displays path statistics
  - Handles errors gracefully
  - Live backend health check

---

## Model Information

### Models Available
1. **GNN (Graph Neural Network)** - Advanced
   - Leverages airport network topology
   - Considers spatial relationships
   - Better for complex paths

2. **Random Forest** - Baseline
   - Ensemble tree-based method
   - Non-linear pattern recognition
   - Fast and interpretable

3. **Ensemble** - Combined
   - Average of GNN and RF predictions
   - Balanced approach
   - Often most reliable

### Current Performance
- **GNN MAE**: ~359 seconds (~6 minutes)
- **RF MAE**: ~361 seconds (~6 minutes)
- **Dataset**: 32 examples from 37 flight files
- **Training**: Convergence achieved (65 epochs)

---

## Troubleshooting

### Backend Not Connecting
- Check Flask is running: `http://localhost:5000/api/health`
- Verify port 5000 is available
- Check firewall settings for localhost access

### Frontend Shows "Backend Disconnected"
- Ensure Flask terminal is still running
- Flask might need ~10 seconds to fully initialize models
- Refresh browser page (Ctrl+R)

### Prediction Errors
- Verify taxiway identifiers exist at KTEB (A-R, L, P, Q)
- Check route format (use hyphens: `A-B-C`)
- Try: `L-C-H` (known good route)

### Model Loading Slow
- GNN initialization takes ~8 seconds on first load
- This is normal - models are cached after first load

---

## Next Steps (Optional)

1. **Production Deployment**
   - Replace Flask dev server with Gunicorn
   - Deploy to cloud (AWS, Azure, Heroku)
   - Add authentication/rate limiting

2. **Enhanced Features**
   - Map visualization of routes
   - Weather integration
   - Aircraft type selection
   - Time-of-day adjustments

3. **Performance Improvement**
   - Collect more training data (1000+ examples)
   - Fine-tune hyperparameters
   - Add additional features (aircraft, weather)

4. **Monitoring**
   - Add request logging
   - Track prediction accuracy vs actual times
   - Monitor model performance over time

---

## Quick Start Commands

```powershell
# Terminal 1: Start Backend (Flask)
cd "c:\Users\priya\OneDrive\Desktop\works\projects\honeyWell\Taxitime-Estimation"
.\.venv\Scripts\python.exe app.py

# Terminal 2: Start Frontend (Next.js)
cd "c:\Users\priya\OneDrive\Desktop\works\projects\honeyWell\Taxitime-Estimation\frontend"
npm run dev

# Open Browser
# http://localhost:3000
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                    │
│              (Port 3000 - localhost:3000)               │
│  • React Component (taxi-time-estimator.tsx)           │
│  • Three Model Cards (GNN, RF, Ensemble)               │
│  • Real-time API calls                                  │
└─────────────────────────────────────────────────────────┘
                            ↓
                    HTTP POST/GET Requests
                            ↓
┌─────────────────────────────────────────────────────────┐
│              Backend API (Flask)                        │
│              (Port 5000 - localhost:5000)               │
│  • /api/predict - Route prediction                     │
│  • /api/health - Status check                          │
│  • /api/taxiways - List available                      │
│  • /api/example-routes - Samples                       │
└─────────────────────────────────────────────────────────┘
                            ↓
                    Python Inference
                            ↓
┌─────────────────────────────────────────────────────────┐
│         Machine Learning Models (PyTorch)              │
│  • GNN Model (Graph Neural Network)                    │
│  • RF Model (Random Forest)                            │
│  • Feature Computation (path_length, turns, etc)       │
│  • Airport Graph (873 vertices, 889 edges)             │
└─────────────────────────────────────────────────────────┘
```

---

**Status**: ✅ FULLY OPERATIONAL
**Last Updated**: December 11, 2025
**System Ready for**: Testing, Demo, or Production Deployment

