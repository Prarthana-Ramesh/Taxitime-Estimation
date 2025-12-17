"""
Flask backend API for Taxi-Time Estimation
Connects to trained GNN and Random Forest models
"""

import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global state for loaded models (lazy loaded)
models = None
airport_graph = None
valid_taxiways = None

def load_predict_modules():
    """Lazy load predict modules to avoid slow networkx imports during startup"""
    global models, airport_graph, valid_taxiways
    from predict import (
        load_models, 
        load_airport_graph, 
        predict_taxi_time, 
        list_available_taxiways
    )
    return load_models, load_airport_graph, predict_taxi_time, list_available_taxiways

def initialize_models():
    """Load models on startup"""
    global models, airport_graph, valid_taxiways
    try:
        print("🔧 Loading predict modules...")
        load_models, load_airport_graph, predict_taxi_time, list_available_taxiways = load_predict_modules()
        
        print("🔧 Loading models...")
        models = load_models()
        print("✅ Models loaded successfully")
        
        print("🔧 Loading airport graph...")
        airport_graph = load_airport_graph()
        print("✅ Airport graph loaded successfully")
        
        valid_taxiways = list_available_taxiways()
        print(f"✅ Valid taxiways: {valid_taxiways}")
    except Exception as e:
        print(f"❌ Error loading models: {str(e)}")
        raise

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Backend API is running",
        "models_loaded": models is not None
    })

@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Predict taxi time for a given route
    
    Expected JSON input:
    {
        "route": "RW27-C3-C-F5-F",
        "model": "gnn" or "rf" or "ensemble" (optional, default: ensemble)
    }
    
    Response:
    {
        "success": true,
        "route": "RW27-C3-C-F5-F",
        "normalized_route": "C-F",
        "predictions": {
            "gnn": 47.0,
            "rf": 67.1,
            "ensemble": 57.0
        },
        "path_stats": {
            "path_length_m": 1234.5,
            "num_turns": 2,
            "sharpness": 45.3
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or "route" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field 'route'"
            }), 400
        
        route = data.get("route", "").upper()
        requested_model = data.get("model", "ensemble").lower()
        
        if not route:
            return jsonify({
                "success": False,
                "error": "Route cannot be empty"
            }), 400
        
        # Validate model choice
        valid_models = ["gnn", "rf", "ensemble"]
        if requested_model not in valid_models:
            return jsonify({
                "success": False,
                "error": f"Invalid model. Choose from: {', '.join(valid_models)}"
            }), 400
        
        # Import predict function when needed
        _, _, predict_taxi_time, _ = load_predict_modules()
        
        # Get prediction
        result = predict_taxi_time(
            route=route,
            models=models,
            airport_graph=airport_graph,
            return_path_stats=True
        )
        
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result.get("error", "Prediction failed")
            }), 400
        
        # Format response based on requested model
        predictions = {}
        if requested_model == "ensemble":
            predictions = {
                "gnn": result["gnn_prediction"],
                "rf": result["rf_prediction"],
                "ensemble": result["ensemble_prediction"]
            }
        elif requested_model == "gnn":
            predictions = {
                "gnn": result["gnn_prediction"]
            }
        elif requested_model == "rf":
            predictions = {
                "rf": result["rf_prediction"]
            }
        
        return jsonify({
            "success": True,
            "route": route,
            "normalized_route": " → ".join(result.get("normalized_route", [route])),
            "predictions": predictions,
            "path_stats": result.get("path_stats", {})
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/taxiways", methods=["GET"])
def get_taxiways():
    """Get list of available taxiways"""
    try:
        return jsonify({
            "success": True,
            "taxiways": valid_taxiways,
            "count": len(valid_taxiways)
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
        {
            "route": "L",
            "description": "Single taxiway"
        },
        {
            "route": "L-C-H",
            "description": "Multi-segment route"
        },
        {
            "route": "RW27-C3-C-F5-F",
            "description": "Complex route with runway and connectors"
        },
        {
            "route": "A-B-C",
            "description": "Sequential taxiways"
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples
    }), 200

if __name__ == "__main__":
    print("🚀 Starting Taxi-Time Estimation Backend API...")
    initialize_models()
    # Disable the reloader which causes networkx import issues on Windows
    app.run(debug=False, host="127.0.0.1", port=5000, use_reloader=False)
