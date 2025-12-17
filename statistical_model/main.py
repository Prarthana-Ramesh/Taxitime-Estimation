from airport_graph import build_graph
from ident_lengths import compute_ident_lengths
from historical_speed import compute_average_speed
from predict import predict_taxi_time

import pandas as pd


# --------------------------------------------
# LOAD VALID IDENTIFIERS FROM EXCEL OR CSV
# -----------------------------------------
def load_valid_idents(file_path):
    # Auto-detect file format
    if file_path.lower().endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, sheet_name="KTEB_Taxiway_Data")

    # Clean column names
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    idents = set(df["Ident"].dropna().unique())

    # Remove invalid items
    idents.discard("$UNK")
    idents.discard("")   # remove blank strings if any

    return idents


# -----------------------------------------------------
# VALIDATE USER PATH
# -----------------------------------------------------
def validate_user_path(path_list, allowed_idents):
    for ident in path_list:
        if ident not in allowed_idents:
            return False, ident
    return True, None


# -----------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------
excel_file = "data_raw/KTEB_Taxiway_Data.csv"

# 1. Load airport graph
G, vertex_dict = build_graph(excel_file)

# 2. Load valid idents
allowed_idents = load_valid_idents(excel_file)
print("Allowed Taxiway Idents:", sorted(allowed_idents))

# 3. Compute lengths per taxiway
ident_lengths = compute_ident_lengths(G)

# 4. Compute average taxi speed
avg_speed = compute_average_speed("data_raw/historical_data.csv")
print(f"Average Taxi Speed: {avg_speed:.2f} m/s")

# 5. Take user input
user_input = input("Enter taxiway path (Example: L-C-H-F): ").strip().upper()
path_list = user_input.split("-")

# 6. Validate
valid, bad_ident = validate_user_path(path_list, allowed_idents)

if not valid:
    print(f"\n❌ ERROR: '{bad_ident}' is NOT a valid taxiway identifier for KTEB.")
    print(f"✔ You may use only these idents: {sorted(allowed_idents)}")
else:
    try:
        distance, time_sec = predict_taxi_time(path_list, ident_lengths, avg_speed)

        print("\n✅ Prediction Successful!")
        print(f"Total Distance: {distance:.2f} meters")
        print(f"Taxi Time: {time_sec:.2f} seconds ({time_sec/60:.2f} minutes)")

    except Exception as e:
        print("❌ Prediction failed:", str(e))
