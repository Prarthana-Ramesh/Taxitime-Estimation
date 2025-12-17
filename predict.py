#!/usr/bin/env python
"""
Predict aircraft taxi time for a specific route at KTEB airport.
Usage:
    python predict.py --route "RW27-C3-C-F5-F"
    python predict.py --list
"""

import torch
import pandas as pd
import numpy as np
import argparse
import joblib
import networkx as nx
from gnn import TaxiTimeGNN
from input_processor import path_to_pyg_data
from utilities import compute_path_length, compute_number_of_turns, compute_sharpness
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'statistical_model'))
from airport_graph import build_graph

def load_models():
    """Load trained models and preprocessors"""
    print("Loading models...")
    
    # Load GNN model with correct parameters
    gnn_model = TaxiTimeGNN(node_in=2, gnn_hidden=64, pool_emb=64, global_feat_dim=3, mlp_hidden=64)
    gnn_model.load_state_dict(torch.load('processed/gnn_model.pt', map_location='cpu'))
    gnn_model.eval()
    
    # Load Random Forest baseline
    rf_model = joblib.load('processed/baseline_rf.joblib')
    
    # Load feature scaler
    scaler_data = np.load('processed/global_feat_scaler.npy', allow_pickle=True).item()
    mean = scaler_data['mean']
    scale = scaler_data['scale']
    
    # Load vertex coordinates
    vertex_coords = torch.load('processed/vertex_index_to_coords.pt')
    
    return gnn_model, rf_model, mean, scale, vertex_coords

def load_airport_graph():
    """Load airport graph and vertex coordinates"""
    print("Loading airport graph...")
    
    # Build graph from Excel file with multiple sheets (uses NetworkX)
    G, vertex_dict = build_graph('data_raw/KTEB_Airport_Data.xlsx')
    
    print(f"  ✓ Loaded {G.number_of_nodes()} vertices")
    print(f"  ✓ Loaded {G.number_of_edges()} edges")
    
    # Build ident->edges mapping
    ident_edges = {}
    for v1, v2, data in G.edges(data=True):
        ident = data.get('Ident', 'Unknown')
        if ident not in ident_edges:
            ident_edges[ident] = []
        ident_edges[ident].append((v1, v2, data['distance']))
    
    return G, vertex_dict, ident_edges

def parse_route_to_vertices(route_string, G, ident_edges, return_normalized=False, verbose=True):
    """
    Parse route string like "RW27-C3-C-F5-F" and find vertex path using graph
    
    Args:
        route_string: Dash or comma-separated taxiway idents
        G: NetworkX graph of airport taxiways
        ident_edges: Dict mapping ident -> list of (v1, v2, distance) tuples
        return_normalized: If True, return (vertex_path, normalized_idents)
        verbose: If True, print debug info
    
    Returns:
        List of vertex indices forming the path, or (path, normalized_idents) if return_normalized=True
    """
    # Handle both comma and dash separators
    if '-' in route_string:
        taxiway_idents = [name.strip().upper() for name in route_string.split('-')]
    else:
        taxiway_idents = [name.strip().upper() for name in route_string.split(',')]
    
    if verbose:
        print(f"📝 Route segments (raw): {' → '.join(taxiway_idents)}")
    
    # Normalize identifiers: strip runway prefix and numbers to get base taxiway letter
    normalized_idents = []
    for ident in taxiway_idents:
        # Remove "RW" prefix for runways
        if ident.startswith('RW'):
            base = ident.replace('RW', '').lstrip('0123456789')
            if not base:
                if verbose:
                    print(f"   ℹ️  Skipping runway designator: {ident}")
                continue
            normalized = base
        else:
            # Extract just the letter part (e.g., C3 -> C, F5 -> F)
            import re
            match = re.match(r'^([A-Z])', ident)
            if match:
                normalized = match.group(1)
            else:
                normalized = ident
        
        # Only add if it exists in database and not duplicate
        if normalized in ident_edges:
            if not normalized_idents or normalized_idents[-1] != normalized:
                normalized_idents.append(normalized)
        elif ident in ident_edges:
            if not normalized_idents or normalized_idents[-1] != ident:
                normalized_idents.append(ident)
    
    if verbose:
        print(f"📝 Route segments (normalized): {' → '.join(normalized_idents)}\n")
    
    # Build path by connecting taxiway segments
    vertex_path = []
    
    for i, ident in enumerate(normalized_idents):
        if ident not in ident_edges:
            if verbose:
                print(f"⚠️  Warning: Taxiway '{ident}' not found in database")
            continue
        
        edges = ident_edges[ident]
        
        if not vertex_path:
            # First segment: pick first edge and add both vertices
            v1, v2, dist = edges[0]
            vertex_path = [v1, v2]
        else:
            # Find edge that connects to current path
            last_vertex = vertex_path[-1]
            found = False
            
            for v1, v2, dist in edges:
                if v1 == last_vertex and v2 not in vertex_path:
                    vertex_path.append(v2)
                    found = True
                    break
                elif v2 == last_vertex and v1 not in vertex_path:
                    vertex_path.append(v1)
                    found = True
                    break
            
            if not found:
                # Try finding shortest path through graph
                for v1, v2, dist in edges:
                    try:
                        if v1 in vertex_path:
                            path = nx.shortest_path(G, vertex_path[-1], v2)
                            vertex_path.extend(path[1:])
                            found = True
                            break
                        elif v2 in vertex_path:
                            path = nx.shortest_path(G, vertex_path[-1], v1)
                            vertex_path.extend(path[1:])
                            found = True
                            break
                    except nx.NetworkXNoPath:
                        continue
            
            if not found and verbose:
                print(f"⚠️  Could not connect '{ident}' to path")
    
    if return_normalized:
        return vertex_path, normalized_idents
    return vertex_path

def predict_taxi_time(route=None, route_string=None, models=None, airport_graph=None, return_path_stats=False, verbose=True):
    """
    Main prediction function
    
    Args:
        route: Route string (preferred parameter name for API)
        route_string: Route string (legacy parameter name for CLI)
        models: Tuple of (gnn_model, rf_model, mean, scale, vertex_coords) - optional, loads if None
        airport_graph: Tuple of (G, vertex_dict, ident_edges) - optional, loads if None
        return_path_stats: If True, returns path statistics in result dict
        verbose: If True, prints results; if False, returns dict only
    
    Returns:
        dict: {
            'success': bool,
            'gnn_prediction': float (seconds),
            'rf_prediction': float (seconds),
            'ensemble_prediction': float (seconds),
            'normalized_route': list of normalized identifiers,
            'path_stats': dict with path_length, num_turns, sharpness,
            'error': str (if failed)
        }
    """
    
    # Handle both parameter names
    route_input = route or route_string
    if not route_input:
        return {'success': False, 'error': 'No route provided'}
    
    # Load models if not provided
    if models is None:
        if verbose:
            print("Loading models...")
        gnn_model, rf_model, mean, scale, vertex_coords = load_models()
    else:
        gnn_model, rf_model, mean, scale, vertex_coords = models
    
    if airport_graph is None:
        if verbose:
            print("Loading airport graph...")
        G, vertex_dict, ident_edges = load_airport_graph()
    else:
        G, vertex_dict, ident_edges = airport_graph
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"🛫 Predicting Taxi Time for Route: {route_input}")
        print(f"{'='*60}\n")
    
    # Parse route to vertex path
    vertex_path, normalized_route = parse_route_to_vertices(route_input, G, ident_edges, return_normalized=True)
    
    if len(vertex_path) < 2:
        error_msg = "Route must have at least 2 vertices. Please check taxiway names."
        if verbose:
            print(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}
    
    if verbose:
        print(f"📍 Vertex Path: {vertex_path[:10]}{'...' if len(vertex_path) > 10 else ''}")
        print(f"🔢 Total Vertices: {len(vertex_path)}\n")
    
    # Build PyG graph using the same function as training
    gnn_time = None
    rf_pred = None
    path_stats = {}
    
    try:
        # Use a dummy taxi time (we're predicting, so actual time doesn't matter)
        graph = path_to_pyg_data(vertex_path, vertex_coords, 0.0)
        
        # Extract features
        path_coords = [vertex_coords[v] for v in vertex_path]
        path_length = compute_path_length(path_coords)
        num_turns = compute_number_of_turns(path_coords)
        sharpness = compute_sharpness(path_coords)
        
        path_stats = {
            'path_length_m': round(path_length, 1),
            'path_length_ft': round(path_length * 3.28084, 0),
            'num_turns': int(num_turns),
            'sharpness': round(sharpness, 2)
        }
        
        if verbose:
            print(f"📏 Path Length: {path_length:.1f} meters ({path_length*3.28084:.0f} feet)")
            print(f"🔄 Number of Turns: {num_turns}")
            print(f"📐 Average Sharpness: {sharpness:.2f}\n")
        
        # GNN Prediction
        with torch.no_grad():
            # Scale global features
            global_feat = torch.tensor([[path_length, num_turns, sharpness]], dtype=torch.float)
            global_feat_scaled = torch.tensor((global_feat.numpy() - mean) / scale, dtype=torch.float)
            
            # Update graph with scaled global features
            graph.global_feat = global_feat_scaled
            
            # Run prediction
            gnn_pred = gnn_model(graph)
            gnn_time = round(gnn_pred.item(), 1)
        
        if verbose:
            print(f"🤖 GNN Model Prediction: {gnn_time:.1f} seconds ({gnn_time/60:.2f} minutes)")
    
    except Exception as e:
        error_msg = f"GNN prediction failed: {e}"
        if verbose:
            print(f"⚠️  {error_msg}")
    
    # Random Forest Prediction
    try:
        # Prepare features for RF (same as GNN global features)
        features = np.array([[path_length, num_turns, sharpness]])
        features_scaled = (features - mean) / scale
        
        rf_pred = round(rf_model.predict(features_scaled)[0], 1)
        if verbose:
            print(f"🌳 Random Forest Prediction: {rf_pred:.1f} seconds ({rf_pred/60:.2f} minutes)")
    
    except Exception as e:
        error_msg = f"Random Forest prediction failed: {e}"
        if verbose:
            print(f"⚠️  {error_msg}")
    
    # Average prediction
    if gnn_time is not None and rf_pred is not None:
        avg_time = round((gnn_time + rf_pred) / 2, 1)
        if verbose:
            print(f"\n📊 Ensemble Average: {avg_time:.1f} seconds ({avg_time/60:.2f} minutes)")
    else:
        avg_time = gnn_time or rf_pred  # Use whichever succeeded
    
    if verbose:
        print(f"\n{'='*60}\n")
    
    # Prepare return dictionary
    result = {
        'success': True,
        'gnn_prediction': gnn_time,
        'rf_prediction': rf_pred,
        'ensemble_prediction': avg_time,
        'normalized_route': normalized_route
    }
    
    if return_path_stats:
        result['path_stats'] = path_stats
    
    return result

def list_available_taxiways():
    """List all available taxiway identifiers"""
    G, vertex_dict, ident_edges = load_airport_graph()
    
    print("\n📋 Available Taxiway Segments at KTEB:")
    print("="*60)
    
    taxiways = sorted(ident_edges.keys())
    
    # Group by type
    runways = [t for t in taxiways if t.startswith('RW')]
    letters = [t for t in taxiways if len(t) == 1 and t.isalpha()]
    others = [t for t in taxiways if t not in runways and t not in letters]
    
    if runways:
        print("\n🛫 Runways:")
        for tw in runways:
            edges = len(ident_edges[tw])
            print(f"  • {tw} ({edges} edge{'s' if edges > 1 else ''})")
    
    if letters:
        print("\n🅰️  Main Taxiways (Single Letter):")
        for tw in letters:
            edges = len(ident_edges[tw])
            print(f"  • {tw} ({edges} edge{'s' if edges > 1 else ''})")
    
    if others:
        print("\n🔤 Other Taxiways:")
        for tw in others:
            edges = len(ident_edges[tw])
            print(f"  • {tw} ({edges} edge{'s' if edges > 1 else ''})")
    
    print(f"\nTotal: {len(taxiways)} unique taxiway identifiers")
    print("\nExample usage:")
    print("  python predict.py --route \"L-C-H-F\"")
    print("  python predict.py --route \"A,B,C\"")
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict aircraft taxi time for a specific route')
    parser.add_argument('--route', type=str, help='Taxiway route (e.g., "L-C-H-F" or "A,B,C")')
    parser.add_argument('--list', action='store_true', help='List all available taxiway segments')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_taxiways()
    elif args.route:
        result = predict_taxi_time(route_string=args.route, verbose=True)
    else:
        print("Usage:")
        print("  python predict.py --route \"L-C-H-F\"")
        print("  python predict.py --list")
        print("\nRun 'python predict.py --list' to see available taxiways.")
