import json

import pandas as pd


def analyze_csv(fileobj) -> dict:
    df = pd.read_csv(fileobj)

    total_rows = len(df)
    missing = {str(col): int(n) for col, n in df.isna().sum().items()}

    numeric = df.select_dtypes(include="number")
    # to_json/json.loads converts numpy types and NaN (-> null) into plain JSON
    numeric_stats = json.loads(numeric.describe().to_json()) if not numeric.empty else {}

    return {
        "row_count": total_rows,
        "column_count": len(df.columns),
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(t) for c, t in df.dtypes.items()},
        "missing_values": missing,
        "total_missing": sum(missing.values()),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_stats": numeric_stats,
    }