from torch_geometric.data import Data, InMemoryDataset
import torch
from utilities import haversine_m, compute_path_length, compute_number_of_turns, compute_sharpness

def path_to_pyg_data(path_vertex_indices, vertex_index_to_coords, target_taxi_time_seconds):
    """
    path_vertex_indices: list of vertex indices along the taxi path in order
    vertex_index_to_coords: dict {vertex_index: (lat,lon)}
    """
    # build nodes list (in order)
    coords = [vertex_index_to_coords[v] for v in path_vertex_indices]
    # node features: lat, lon (we will normalize later globally)
    x = torch.tensor(coords, dtype=torch.float)  # shape [N,2]
    # edges (bidirectional)
    edge_index_list = [[], []]
    edge_attr_list = []
    for i in range(len(coords)-1):
        a = i
        b = i+1
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i+1]
        length = haversine_m(lat1, lon1, lat2, lon2)
        # add both directions
        edge_index_list[0] += [a, b]
        edge_index_list[1] += [b, a]
        edge_attr_list += [[length],[length]]

    edge_index = torch.tensor(edge_index_list, dtype=torch.long)
    edge_attr = torch.tensor(edge_attr_list, dtype=torch.float) if edge_attr_list else None

    # compute global features
    path_length = compute_path_length(coords)
    num_turns = compute_number_of_turns(coords)
    sharpness = compute_sharpness(coords)
    global_feats = torch.tensor([path_length, num_turns, sharpness], dtype=torch.float).unsqueeze(0)

    y = torch.tensor([target_taxi_time_seconds], dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    # attach global features as Data.u (or data.global_feat)
    data.global_feat = global_feats  # shape [1,3]
    return data
