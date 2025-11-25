import pandas as pd


def compute_average_speed(file_path):
    """Read historical data robustly and compute mean landing speed.

    Tries to read as an Excel file using `openpyxl` engine first. If that
    fails (file misnamed or engine missing), falls back to `read_csv`.
    Raises a clear error if required columns are missing.
    """
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception:
        # Fallback: file might be CSV or an Excel engine is not available
        df = pd.read_csv(file_path)

    required = {"phase", "Speed", "time"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required columns in {file_path}: {missing}")

    clean = df[
        (df["phase"] == "landing") &
        (df["Speed"] > 1) &
        (df["Speed"] < 40) &
        (df["time"] > 1)
    ].copy()

    avg_speed = clean["Speed"].mean()
    return avg_speed
