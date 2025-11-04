import pandas as pd
from smart_preprocess import SmartCleaner

def test_fit_transform_runs():
    df = pd.DataFrame({
        "age": [20, 21, None, 23, 1000],   # has missing + outlier
        "city": ["A", "B", "A", None, "C"]
    })
    cl = SmartCleaner(outlier_clip=True)
    X = cl.fit_transform(df)

    # sanity checks
    assert X.shape[0] == 5
    assert "age__scaled" in X.columns
    assert any(col.startswith("city_") for col in X.columns)
