from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _iqr_clip(df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
    """Clip outliers using the IQR rule."""
    clipped = df.copy()
    for col in numeric_cols:
        q1 = clipped[col].quantile(0.25)
        q3 = clipped[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        clipped[col] = clipped[col].clip(lower, upper)
    return clipped


@dataclass
class SmartCleaner:
    outlier_clip: bool = True
    handle_unknown: str = "ignore"
    _is_fit: bool = field(default=False, init=False)
    _numeric_cols: List[str] = field(default_factory=list, init=False)
    _categorical_cols: List[str] = field(default_factory=list, init=False)
    _ct: Optional[ColumnTransformer] = field(default=None, init=False)
    report_: Dict[str, Any] = field(default_factory=dict, init=False)

    def _split_cols(self, df: pd.DataFrame):
        num = df.select_dtypes(include=[np.number]).columns.tolist()
        cat = [c for c in df.columns if c not in num]
        return num, cat

    def fit(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")
        X = df.copy()
        self._numeric_cols, self._categorical_cols = self._split_cols(X)

        if self.outlier_clip and self._numeric_cols:
            X = _iqr_clip(X, self._numeric_cols)

        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        cat_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown=self.handle_unknown, sparse_output=False))
        ])

        transformers = []
        if self._numeric_cols:
            transformers.append(("num", num_pipe, self._numeric_cols))
        if self._categorical_cols:
            transformers.append(("cat", cat_pipe, self._categorical_cols))

        self._ct = ColumnTransformer(transformers)
        self._ct.fit(X)

        self.report_ = {
            "numeric_cols": self._numeric_cols,
            "categorical_cols": self._categorical_cols,
            "outlier_clip": self.outlier_clip,
            "impute_numeric": "median",
            "impute_categorical": "most_frequent",
            "scale_numeric": True,
            "encode_categorical": "one-hot"
        }
        self._is_fit = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._is_fit:
            raise RuntimeError("Call fit() before transform().")
        X = df.copy()
        if self.outlier_clip and self._numeric_cols:
            X = _iqr_clip(X, self._numeric_cols)
        arr = self._ct.transform(X)

        cols = []
        if self._numeric_cols:
            cols += [f"{c}__scaled" for c in self._numeric_cols]
        if self._categorical_cols:
            encoder: OneHotEncoder = self._ct.named_transformers_["cat"].named_steps["encoder"]
            cols += encoder.get_feature_names_out(self._categorical_cols).tolist()

        return pd.DataFrame(arr, columns=cols, index=df.index)

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
