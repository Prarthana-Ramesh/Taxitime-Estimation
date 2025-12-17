# Quick Start Guide 🚀

## Current Status ✅
- **Backend API**: Running on `http://127.0.0.1:5000` 
- **Frontend UI**: Running on `http://localhost:3000`
- **Models**: GNN + Random Forest loaded
- **Ready**: YES

---

## Access the System

### Open in Browser
👉 **http://localhost:3000**

---

## How to Use

### Method 1: Web Interface (Easiest)
1. Go to http://localhost:3000
2. Enter a route: `L-C-H` or `RW27-C3-C-F5-F`
3. Click "Estimate Taxi Time"
4. View results in real-time with path statistics

### Method 2: Command Line
```powershell
python predict.py --route "L-C-H"
python predict.py --list
```

### Method 3: API (Advanced)
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"route":"L-C-H","model":"ensemble"}'
```

---

## Example Routes to Try

| Route | Type | Expected Result |
|-------|------|-----------------|
| `L` | Single taxiway | Quick result |
| `L-C-H` | Multi-segment | ~50-70 seconds |
| `RW27-C3-C-F5-F` | Complex | ~50-70 seconds |
| `A-B-C` | Sequential | ~40-60 seconds |
| `C-F` | Direct | ~30-50 seconds |

---

## Keep Systems Running

### Terminal 1: Backend
```powershell
cd "Taxitime-Estimation"
.\.venv\Scripts\python.exe app.py
```
Status: Running on http://127.0.0.1:5000

### Terminal 2: Frontend
```powershell
cd "Taxitime-Estimation\frontend"
npm run dev
```
Status: Running on http://localhost:3000

---

## Available Taxiways at KTEB

🟢 **Main**: A, B, C, D, E, F, G, H, J, K, L, P, Q, R

---

## What Each Model Does

| Model | Type | Best For |
|-------|------|----------|
| **GNN** | Deep Learning (Graph) | Complex paths, spatial relationships |
| **Random Forest** | Ensemble (Trees) | Fast, interpretable predictions |
| **Mean** (Ensemble) | Combined Average | Balanced, often most reliable |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend shows disconnected | Restart Flask (Ctrl+C, then re-run) |
| Page won't load | Check if http://localhost:3000 is accessible |
| API returns error | Verify Flask is running on port 5000 |
| Routes not found | Use valid taxiway letters (A-R, L, P, Q) |

---

## Files to Know

- **Backend**: `app.py` - Flask server
- **Frontend**: `frontend/components/taxi-time-estimator.tsx` - React component
- **Models**: `processed/gnn_model.pt`, `processed/baseline_rf.joblib`
- **Data**: `data_raw/KTEB_Airport_Data.xlsx`

---

## URLs to Bookmark

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Web UI |
| http://127.0.0.1:5000/api/health | Health check |
| http://127.0.0.1:5000/api/taxiways | List available taxiways |

---

## Quick Verification

**Is everything working?**

1. Frontend loads at http://localhost:3000 ✅
2. Backend shows "Running on http://127.0.0.1:5000" ✅
3. Try route "L-C-H" in the web interface ✅
4. See predictions within 1-2 seconds ✅

**If all above work**: System is READY! 🎉

---

## Need Help?

1. Check terminal output for error messages
2. Ensure both Flask and Next.js are running
3. Refresh browser (Ctrl+R)
4. Verify routes use valid taxiway letters
5. Check INTEGRATION_COMPLETE.md for detailed docs

---

**Last Updated**: December 11, 2025  
**System Status**: ✅ Production Ready
