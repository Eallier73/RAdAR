from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.model_selection import TimeSeriesSplit


class SarimaxRegressor(BaseEstimator, RegressorMixin):
    def __init__(
        self,
        order: tuple[int, int, int] = (1, 0, 0),
        trend: str = "c",
        maxiter: int = 200,
        enforce_stationarity: bool = False,
        enforce_invertibility: bool = False,
    ) -> None:
        self.order = order
        self.trend = trend
        self.maxiter = maxiter
        self.enforce_stationarity = enforce_stationarity
        self.enforce_invertibility = enforce_invertibility

    def fit(self, x, y):
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        x_df = pd.DataFrame(x).copy()
        self.feature_names_in_ = list(x_df.columns)
        exog = x_df if not x_df.empty else None
        self.model_ = SARIMAX(
            endog=np.asarray(y, dtype=float),
            exog=exog,
            order=self.order,
            trend=self.trend,
            enforce_stationarity=self.enforce_stationarity,
            enforce_invertibility=self.enforce_invertibility,
        )
        self.results_ = self.model_.fit(disp=False, maxiter=self.maxiter)
        return self

    def predict(self, x):
        x_df = pd.DataFrame(x, columns=getattr(self, "feature_names_in_", None)).copy()
        exog = x_df if not x_df.empty else None
        forecast = self.results_.forecast(steps=len(x_df), exog=exog)
        return np.asarray(forecast, dtype=float)


class ProphetExogenousRegressor(BaseEstimator, RegressorMixin):
    def __init__(
        self,
        date_column: str,
        changepoint_prior_scale: float = 0.05,
        seasonality_mode: str = "additive",
        weekly_seasonality: bool = False,
        yearly_seasonality: bool = False,
        daily_seasonality: bool = False,
    ) -> None:
        self.date_column = date_column
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_mode = seasonality_mode
        self.weekly_seasonality = weekly_seasonality
        self.yearly_seasonality = yearly_seasonality
        self.daily_seasonality = daily_seasonality

    def fit(self, x, y):
        from prophet import Prophet

        x_df = pd.DataFrame(x).copy()
        if self.date_column not in x_df.columns:
            raise ValueError(f"Prophet requiere la columna de fecha '{self.date_column}'.")

        self.regressor_columns_ = [column for column in x_df.columns if column != self.date_column]
        train_df = pd.DataFrame(
            {
                "ds": pd.to_datetime(x_df[self.date_column]),
                "y": np.asarray(y, dtype=float),
            }
        )
        for column in self.regressor_columns_:
            train_df[column] = x_df[column].to_numpy()

        self.model_ = Prophet(
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_mode=self.seasonality_mode,
            weekly_seasonality=self.weekly_seasonality,
            yearly_seasonality=self.yearly_seasonality,
            daily_seasonality=self.daily_seasonality,
        )
        for column in self.regressor_columns_:
            self.model_.add_regressor(column)

        self.model_.fit(train_df)
        return self

    def predict(self, x):
        x_df = pd.DataFrame(x).copy()
        future_df = pd.DataFrame({"ds": pd.to_datetime(x_df[self.date_column])})
        for column in self.regressor_columns_:
            future_df[column] = x_df[column].to_numpy()
        forecast = self.model_.predict(future_df)
        return forecast["yhat"].to_numpy(dtype=float)


class ResidualHybridRegressor(BaseEstimator, RegressorMixin):
    def __init__(self, base_estimator, residual_estimator) -> None:
        self.base_estimator = base_estimator
        self.residual_estimator = residual_estimator

    def fit(self, x, y):
        self.base_estimator_ = clone(self.base_estimator)
        self.base_estimator_.fit(x, y)
        base_predictions = np.asarray(self.base_estimator_.predict(x), dtype=float)
        residuals = np.asarray(y, dtype=float) - base_predictions
        self.residual_estimator_ = clone(self.residual_estimator)
        self.residual_estimator_.fit(x, residuals)
        return self

    def predict(self, x):
        base_predictions = np.asarray(self.base_estimator_.predict(x), dtype=float)
        residual_predictions = np.asarray(self.residual_estimator_.predict(x), dtype=float)
        return base_predictions + residual_predictions


class TimeSeriesStackingRegressor(BaseEstimator, RegressorMixin):
    def __init__(
        self,
        base_estimators: Sequence[tuple[str, object]],
        final_estimator,
        n_splits: int = 3,
        min_train_size: int = 12,
    ) -> None:
        self.base_estimators = tuple(base_estimators)
        self.final_estimator = final_estimator
        self.n_splits = n_splits
        self.min_train_size = min_train_size

    def fit(self, x, y):
        x_df = pd.DataFrame(x).reset_index(drop=True)
        y_array = np.asarray(y, dtype=float)
        self.fitted_base_estimators_ = []
        self.fallback_average_ = False

        if len(x_df) < max(self.min_train_size + 1, 6):
            self.fallback_average_ = True
            for name, estimator in self.base_estimators:
                fitted = clone(estimator)
                fitted.fit(x_df, y_array)
                self.fitted_base_estimators_.append((name, fitted))
            return self

        max_splits = min(self.n_splits, len(x_df) - 1)
        if max_splits < 2:
            self.fallback_average_ = True
            for name, estimator in self.base_estimators:
                fitted = clone(estimator)
                fitted.fit(x_df, y_array)
                self.fitted_base_estimators_.append((name, fitted))
            return self

        splitter = TimeSeriesSplit(n_splits=max_splits)
        meta_features = np.full((len(x_df), len(self.base_estimators)), np.nan, dtype=float)

        for train_idx, valid_idx in splitter.split(x_df):
            if len(train_idx) < self.min_train_size:
                continue
            x_train = x_df.iloc[train_idx]
            x_valid = x_df.iloc[valid_idx]
            y_train = y_array[train_idx]

            for est_idx, (_, estimator) in enumerate(self.base_estimators):
                fitted = clone(estimator)
                fitted.fit(x_train, y_train)
                meta_features[valid_idx, est_idx] = np.asarray(
                    fitted.predict(x_valid),
                    dtype=float,
                )

        valid_mask = ~np.isnan(meta_features).any(axis=1)
        if int(valid_mask.sum()) < max(2, len(self.base_estimators)):
            self.fallback_average_ = True
            for name, estimator in self.base_estimators:
                fitted = clone(estimator)
                fitted.fit(x_df, y_array)
                self.fitted_base_estimators_.append((name, fitted))
            return self

        self.final_estimator_ = clone(self.final_estimator)
        self.final_estimator_.fit(meta_features[valid_mask], y_array[valid_mask])

        for name, estimator in self.base_estimators:
            fitted = clone(estimator)
            fitted.fit(x_df, y_array)
            self.fitted_base_estimators_.append((name, fitted))
        return self

    def predict(self, x):
        x_df = pd.DataFrame(x).reset_index(drop=True)
        meta_matrix = np.column_stack(
            [
                np.asarray(fitted.predict(x_df), dtype=float)
                for _, fitted in self.fitted_base_estimators_
            ]
        )
        if self.fallback_average_:
            return meta_matrix.mean(axis=1)
        return np.asarray(self.final_estimator_.predict(meta_matrix), dtype=float)
