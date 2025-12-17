#!/usr/bin/env python
"""
Simplified Flask server that starts faster by avoiding immediate imports
"""
import sys
import os

# Set environment variable to speed up imports
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Lazy-loaded globals
_models = None
_airport_graph = None

def get_models():
    """Lazy load models on first use"""
    global _models, _airport_graph
    if _models is None:
        print("💾 Loading ML models (first request)...")
        from predict import load_models, load_airport_graph
        _models = load_models()
        _airport_graph = load_airport_graph()
        print("✅ Models loaded")
    return _models, _airport_graph

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Backend API is running",
        "models_loaded": _models is not None
    }), 200

@app.route("/api/predict", methods=["POST"])
def predict():
    """Make predictions"""
    try:
        data = request.get_json()
        
        if not data or "route" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field 'route'"
            }), 400
        
        route = data.get("route", "").upper()
        
        if not route:
            return jsonify({
                "success": False,
                "error": "Route cannot be empty"
            }), 400
        
        # Load models on first request
        models, airport_graph = get_models()
        
        # Import predict function
        from predict import predict_taxi_time
        
        # Get prediction
        result = predict_taxi_time(
            route=route,
            models=models,
            airport_graph=airport_graph,
            return_path_stats=True,
            verbose=False
        )
        
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result.get("error", "Prediction failed")
            }), 400
        
        requested_model = data.get("model", "ensemble").lower()
        
        # Format predictions
        if requested_model == "ensemble":
            predictions = {
                "gnn": result["gnn_prediction"],
                "rf": result["rf_prediction"],
                "ensemble": result["ensemble_prediction"]
            }
        elif requested_model == "gnn":
            predictions = {"gnn": result["gnn_prediction"]}
        elif requested_model == "rf":
            predictions = {"rf": result["rf_prediction"]}
        else:
            predictions = {
                "gnn": result["gnn_prediction"],
                "rf": result["rf_prediction"],
                "ensemble": result["ensemble_prediction"]
            }
        
        return jsonify({
            "success": True,
            "route": route,
            "normalized_route": " → ".join(result.get("normalized_route", [route])),
            "predictions": predictions,
            "path_stats": result.get("path_stats", {})
        }), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/taxiways", methods=["GET"])
def get_taxiways():
    """Get list of available taxiways"""
    try:
        models, airport_graph = get_models()
        from predict import list_available_taxiways
        taxiways = list_available_taxiways()
        
        return jsonify({
            "success": True,
            "taxiways": taxiways if taxiways else ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "P", "Q", "R"],
            "count": len(taxiways) if taxiways else 15
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/example-routes", methods=["GET"])
def get_example_routes():
    """Get example routes for demonstration"""
    examples = [
        {"route": "L", "description": "Single taxiway"},
        {"route": "L-C-H", "description": "Multi-segment route"},
        {"route": "RW27-C3-C-F5-F", "description": "Complex route with runway"},
        {"route": "A-B-C", "description": "Sequential taxiways"}
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    }), 200

if __name__ == "__main__":
    print("🚀 Starting Taxi-Time Estimation Backend...")
    print("⏳ Models will load on first request (faster startup)")
    print("🌐 Listening on http://127.0.0.1:5000")
    app.run(debug=False, host="127.0.0.1", port=5000, use_reloader=False, threaded=True)
