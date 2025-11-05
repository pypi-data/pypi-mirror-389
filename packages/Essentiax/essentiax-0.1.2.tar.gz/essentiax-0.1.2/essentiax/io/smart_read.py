import pandas as pd
import os
import csv

def smart_read(path, dropna=False, fillna=None):
    """Smart CSV/Excel Reader with:
    - Automatic delimiter detection (for CSV)
    - Missing value handling (dropna/fillna)
    - Data type and shape inspection
    - Quick dataset overview (mini-EDA)
    
    Args:
        path (str): File path (.csv or .xlsx)
        dropna (bool): If True, drops rows with missing values
        fillna (any): Value to fill missing cells (e.g., 0, "Unknown")
    """
    try:
        print(f"[Essentia] Reading file: {path}")

        ext = os.path.splitext(path)[1].lower()

        # Auto-detect file type
        if ext == ".csv":
            # Auto-detect delimiter
            with open(path, 'r', encoding='utf-8') as f:
                sample = f.read(2048)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                print(f"[Essentia] Detected delimiter: '{delimiter}'")
            
            df = pd.read_csv(path, delimiter=delimiter)

        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(path)

        else:
            print("[Essentia] ❌ Unsupported file type.")
            return None

        print(f"[Essentia] ✅ Loaded successfully with shape {df.shape}")
        print("[Essentia] Column Data Types:")
        print(df.dtypes)

        # Missing value detection
        missing = df.isnull().sum()
        missing_cols = missing[missing > 0]

        if not missing_cols.empty:
            print("[Essentia] ⚠ Missing Values Found:")
            print(missing_cols)

            if dropna:
                df = df.dropna()
                print("[Essentia] 🧹 Dropped rows with missing values.")
            elif fillna is not None:
                df = df.fillna(fillna)
                print(f"[Essentia] 🧹 Filled missing values with '{fillna}'.")
        else:
            print("[Essentia] ✅ No Missing Values Found.")

        # 🔎 Quick Data Overview (Mini EDA)
        print("\n[Essentia] 🔍 Quick Dataset Overview")
        print("--------------------------------------------------")
        print("[Essentia] 🔹 First 5 Rows:")
        print(df.head())
        print("--------------------------------------------------")
        print("[Essentia] 🔹 Shape:", df.shape)
        print("[Essentia] 🔹 Columns:", list(df.columns))
        print("--------------------------------------------------")
        print("[Essentia] 🔹 Descriptive Statistics:")
        print(df.describe(include='all'))
        print("--------------------------------------------------")

        return df

    except FileNotFoundError:
        print(f"[Essentia] ❌ File not found: {path}")
        return None
    except Exception as e:
        print(f"[Essentia] ❌ Error reading file: {e}")
        return None
