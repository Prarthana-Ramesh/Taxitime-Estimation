import pandas as pd
import glob
import os
root = r"C:\Users\priya\OneDrive\Desktop\works\projects\honeyWell"
for p in glob.glob(os.path.join(root, '*.xlsx')):
    print('\nFILE:', p)
    try:
        xl = pd.read_excel(p)
        cols = list(xl.columns)
        print('Columns:', cols)
        low = [c.lower() for c in cols]
        if any('lat' in c for c in low) and any('lon' in c for c in low):
            print('-> Likely vertex-like sheet. Showing head:')
            print(xl.head(5).to_csv(index=False))
    except Exception as e:
        print('ERR', e)
