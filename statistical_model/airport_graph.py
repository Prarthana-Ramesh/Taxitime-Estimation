import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2


def haversine(p1, p2):
    """Returns distance in meters between two (lon, lat) points."""
    lon1, lat1 = p1
    lon2, lat2 = p2

    R = 6371000
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def build_graph(excel_file):
    """Builds a NetworkX graph from the airport Excel file."""
    
    # Load data
    taxiway_data = pd.read_excel(excel_file, sheet_name="KTEB_Taxiway_Data")
    vertex_data = pd.read_excel(excel_file, sheet_name="KTEB_Vertex_Data")

    # Clean column names
    taxiway_data.columns = taxiway_data.columns.str.strip().str.replace(" ", "_")
    vertex_data.columns = vertex_data.columns.str.strip().str.replace(" ", "_")

    # Create vertex lookup dictionary
    vertex_dict = dict(
        zip(vertex_data["Vertex_Index"], zip(vertex_data["Longitude"], vertex_data["Latitude"]))
    )

    # Initialize graph
    G = nx.Graph()

    # Add edges
    for idx, row in taxiway_data.iterrows():
        try:
            vertices = [
                int(v.strip()) for v in str(row["Vertex_Indices"]).split(",")
                if v.strip().isdigit()
            ]

            for i in range(len(vertices) - 1):
                v1, v2 = vertices[i], vertices[i + 1]

                if v1 in vertex_dict and v2 in vertex_dict:
                    p1 = vertex_dict[v1]
                    p2 = vertex_dict[v2]

                    distance = haversine(p1, p2)

                    G.add_edge(
                        v1, v2,
                        Ident=row.get("Ident", "Unknown"),
                        distance=distance
                    )

        except Exception as e:
            print(f"Skipping row {idx} due to error: {e}")

    return G, vertex_dict


def plot_graph(G, vertex_dict, output_dir="Taxiway_Graph_Images"):
    """Plots and saves the airport graph."""

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    pos = {v: (lon, lat) for v, (lon, lat) in vertex_dict.items()}

    plt.figure(figsize=(12, 12))
    nx.draw(
        G,
        pos,
        node_size=5,
        node_color='blue',
        edge_color='gray',
        with_labels=False
    )

    plt.title("KTEB Airport Taxiway Graph (Lat/Lon Layout)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    save_path = os.path.join(output_dir, f"KTEB_Taxiway_Graph_{timestamp}.png")
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    return save_path
