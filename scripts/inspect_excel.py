import pandas as pd
import sys
p = r"C:\Users\priya\OneDrive\Desktop\works\projects\honeyWell\KTEB_Airport_Data (1).xlsx"
try:
    df = pd.read_excel(p)
    print('SUCCESS: loaded Excel')
    print('Columns:', list(df.columns))
    print(df.head(5).to_csv(index=False))
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
