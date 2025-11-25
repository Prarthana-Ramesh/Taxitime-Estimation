import math
import numpy as np

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def compute_path_length(vertices):
    total = 0.0
    for i in range(len(vertices)-1):
        total += haversine_m(vertices[i][0], vertices[i][1],
                             vertices[i+1][0], vertices[i+1][1])
    return total

def compute_turn_angles(vertices):
    angles = []
    for i in range(1, len(vertices)-1):
        a, b, c = vertices[i-1], vertices[i], vertices[i+1]
        d1 = haversine_m(a[0], a[1], b[0], b[1]) + 1e-9
        d2 = haversine_m(b[0], b[1], c[0], c[1]) + 1e-9
        v1m = ( (b[0]-a[0])/d1, (b[1]-a[1])/d1 )
        v2m = ( (c[0]-b[0])/d2, (c[1]-b[1])/d2 )
        dot = v1m[0]*v2m[0] + v1m[1]*v2m[1]
        dot = max(min(dot, 1.0), -1.0)
        ang = math.degrees(math.acos(dot))
        angles.append(abs(ang))
    return angles

def compute_number_of_turns(vertices, threshold_deg=10.0):
    angles = compute_turn_angles(vertices)
    return sum(1 for a in angles if a > threshold_deg)

def compute_sharpness(vertices):
    angles = compute_turn_angles(vertices)
    if len(angles)==0:
        return 0.0
    return float(np.mean(angles))