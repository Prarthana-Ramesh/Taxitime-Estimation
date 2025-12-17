import os
import sys
import torch
# Ensure project root is on sys.path so imports from repo resolve when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from input_processor import path_to_pyg_data

# Create a small synthetic vertex map
vertex_index_to_coords = {
    1: (40.8500, -74.0600),
    2: (40.8510, -74.0590),
    3: (40.8520, -74.0580),
    4: (40.8530, -74.0570),
    5: (40.8540, -74.0560),
    6: (40.8550, -74.0550),
}

# Define a few paths (vertex indices) and synthetic taxi times (seconds)
paths = [
    ([1,2,3], 120.0),
    ([2,3,4,5], 180.0),
    ([1,3,5], 210.0),
    ([3,4,5,6], 150.0),
    ([1,2], 60.0),
]

dataset_list = []
for path, t in paths:
    try:
        data = path_to_pyg_data(path, vertex_index_to_coords, t)
        dataset_list.append(data)
    except Exception as e:
        print('Error creating example:', e)

os.makedirs('processed', exist_ok=True)
torch.save(dataset_list, 'processed/dataset_list.pt')
torch.save(vertex_index_to_coords, 'processed/vertex_index_to_coords.pt')
print('Saved synthetic dataset with', len(dataset_list), 'examples')
