from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, RobustScaler, StandardScaler

from config import (
    TRANSFORM_MODE_NONE,
    TRANSFORM_MODE_ROBUST,
    TRANSFORM_MODE_STANDARD,
    TRANSFORM_MODE_WINSOR,
)


class Winsorizer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        lower_quantile: float = 0.05,
        upper_quantile: float = 0.95,
    ) -> None:
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile

    def fit(self, x, y=None):
        values = np.asarray(x, dtype=float)
        self.lower_bounds_ = np.nanquantile(values, self.lower_quantile, axis=0)
        self.upper_bounds_ = np.nanquantile(values, self.upper_quantile, axis=0)
        return self

    def transform(self, x):
        values = np.asarray(x, dtype=float)
        return np.clip(values, self.lower_bounds_, self.upper_bounds_)


def build_feature_transformer(
    *,
    transform_mode: str,
    winsor_lower_quantile: float = 0.05,
    winsor_upper_quantile: float = 0.95,
):
    if transform_mode == TRANSFORM_MODE_NONE:
        return FunctionTransformer(validate=False)
    if transform_mode == TRANSFORM_MODE_STANDARD:
        return StandardScaler()
    if transform_mode == TRANSFORM_MODE_ROBUST:
        return RobustScaler()
    if transform_mode == TRANSFORM_MODE_WINSOR:
        return Pipeline(
            steps=[
                (
                    "winsorizer",
                    Winsorizer(
                        lower_quantile=winsor_lower_quantile,
                        upper_quantile=winsor_upper_quantile,
                    ),
                ),
                ("scaler", StandardScaler()),
            ]
        )
    raise ValueError(f"Transform mode no soportado: {transform_mode}")


def describe_transform_mode(transform_mode: str) -> str:
    descriptions = {
        TRANSFORM_MODE_NONE: "sin_transformacion",
        TRANSFORM_MODE_STANDARD: "standard_scaler",
        TRANSFORM_MODE_ROBUST: "robust_scaler",
        TRANSFORM_MODE_WINSOR: "winsor_05_95_plus_standard_scaler",
    }
    return descriptions[transform_mode]
