from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_selection import mutual_info_regression

#Feature engineering to lag and roll the features so it will be past data and there won't be any data leakage and making a new feature of pice change ratio
class TimeFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Features for next-step prediction (y at t+1):
      - price_ratio(t) = high/low
      - lags: shift(+k) for selected columns
      - rolling stats: mean/std/min/max over past window
    """
    def __init__(self, 
                 base_cols=('open','low','close','volume','count'),
                 lags=(1,3,7),
                 roll_windows=(3,7,14),
                 add_price_ratio=True,
                 keep_raw=True,
                 drop_na=True):
        self.base_cols = base_cols
        self.lags = lags
        self.roll_windows = roll_windows
        self.add_price_ratio = add_price_ratio
        self.keep_raw = keep_raw
        self.drop_na = drop_na
        self.cols_out_ = None
        self.last_index_ = None 

    def fit(self, X, y=None):
        X = pd.DataFrame(X)
        present = [c for c in self.base_cols if c in X.columns]
        cols = []
        if self.add_price_ratio and {'high','low'}.issubset(X.columns):
            cols.append('price_ratio')
        for c in present:
            for k in self.lags:
                cols.append(f'{c}_lag{k}')
            for w in self.roll_windows:
                cols += [f'{c}_r{w}_mean', f'{c}_r{w}_std', f'{c}_r{w}_min', f'{c}_r{w}_max']
        if self.keep_raw:
            cols += present
        self.cols_out_ = cols
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        feats = pd.DataFrame(index=X.index)

        present = [c for c in self.base_cols if c in X.columns]

        # price_ratio = high / low
        if self.add_price_ratio and {'high','low'}.issubset(X.columns):
            denom = X['low'].replace(0, np.nan)
            feats['price_ratio'] = X['high'] / denom

        # lags
        for c in present:
            for k in self.lags:
                feats[f'{c}_lag{k}'] = X[c].shift(k)

        # rolling stats (current-inclusive; safe for y at t+1)
        for c in present:
            for w in self.roll_windows:
                r = X[c].rolling(window=w, min_periods=w)
                feats[f'{c}_r{w}_mean'] = r.mean()
                feats[f'{c}_r{w}_std']  = r.std()
                feats[f'{c}_r{w}_min']  = r.min()
                feats[f'{c}_r{w}_max']  = r.max()

        if self.keep_raw:
            feats[present] = X[present]

        if self.drop_na:
            feats = feats.dropna()

        self.cols_out_ = feats.columns.tolist()
        self.last_index_ = feats.index          
        return feats

    def get_feature_names_out(self, input_features=None):
        return np.array(self.cols_out_ or [])

    # align targets to the rows kept
    def align_y(self, y):
        if self.last_index_ is None:
            raise RuntimeError("Call transform() before align_y().")
        return pd.Series(y).loc[self.last_index_]
    
    #Making a pipeline for any future data, so it needs to be sorted by time and if there is any duplicates it should be dropped
class EnsureTimeAndDedup(BaseEstimator, TransformerMixin):
    def __init__(self, time_col='time', dedup_on_time=True, drop_full_duplicates=True,
                 keep='first', drop_time=False):
        self.time_col = time_col
        self.dedup_on_time = dedup_on_time
        self.drop_full_duplicates = drop_full_duplicates
        self.keep = keep
        self.drop_time = drop_time
        self.last_index_ = None  

    def fit(self, X, y=None):
        if self.time_col not in X.columns:
            raise KeyError(f"Missing time column: {self.time_col}")
        return self

    def transform(self, X):
        df = X.copy()
        df[self.time_col] = pd.to_datetime(df[self.time_col], utc=True, errors='raise')
        df = df.sort_values(self.time_col)
        if self.dedup_on_time:
            df = df[~df[self.time_col].duplicated(keep=self.keep)]
        if self.drop_full_duplicates:
            df = df.drop_duplicates(keep=self.keep)
        if self.drop_time and self.time_col in df.columns:
            df = df.drop(columns=[self.time_col])
        self.last_index_ = df.index  
        return df

    # align y to the rows kept
    def align_y(self, y):
        if self.last_index_ is None:
            raise RuntimeError("Call transform() before align_y().")
        return pd.Series(y).loc[self.last_index_]
    
    #Mutual information for feature selection without any assumption regarding the relationship
class MIRegSelector(BaseEstimator, TransformerMixin):
    """Top-k by mutual information with continuous y."""
    def __init__(self, k=40, n_neighbors=5, random_state=42):
        self.k = int(k); self.n_neighbors = int(n_neighbors); self.random_state = random_state
        self.selected_columns_ = None
        self.scores_ = None

    def fit(self, X, y):
        X = pd.DataFrame(X); y = pd.Series(y).astype(float)
        scores = mutual_info_regression(
            X.values, y.values, n_neighbors=self.n_neighbors, random_state=self.random_state
        )
        self.scores_ = pd.Series(scores, index=X.columns).sort_values(ascending=False)
        self.selected_columns_ = self.scores_.head(self.k).index.tolist()
        return self

    def transform(self, X):
        X = pd.DataFrame(X)
        return X[self.selected_columns_]

    def get_feature_names_out(self, input_features=None):
        return np.array(self.selected_columns_)
    
    #correlation to find the linear relationship

class CorrSelector(BaseEstimator, TransformerMixin):
    """
    Top-k by |corr(y)| (Pearson or Spearman), then drop collinear features (> threshold)
    keeping the ones more correlated to y.
    """
    def __init__(self, k=40, method='pearson', drop_collinear=True, collinear_threshold=0.92):
        assert method in ('pearson', 'spearman')
        self.k = int(k); self.method = method
        self.drop_collinear = drop_collinear; self.collinear_threshold = float(collinear_threshold)
        self.selected_columns_ = None
        self.rank_ = None  # |corr(y)| series

    def fit(self, X, y):
        X = pd.DataFrame(X); y = pd.Series(y).astype(float)
        corr_to_y = X.corrwith(y, method=self.method).abs()
        ordered = corr_to_y.sort_values(ascending=False)
        top = list(ordered.head(self.k).index)

        if self.drop_collinear and len(top) > 1:
            sub = X[top]
            ff = sub.corr(method=self.method).abs()
            keep, dropped = [], set()
            for f in ordered.index:  # strongest to weakest
                if f not in top or f in dropped:
                    continue
                keep.append(f)
                collinear = ff.index[(ff[f] > self.collinear_threshold)].tolist()
                if f in collinear: collinear.remove(f)
                dropped.update(collinear)
            selected = keep
        else:
            selected = top

        self.selected_columns_ = selected
        self.rank_ = ordered
        return self

    def transform(self, X):
        X = pd.DataFrame(X)
        return X[self.selected_columns_]

    def get_feature_names_out(self, input_features=None):
        return np.array(self.selected_columns_)
    
    #Combine the features from both correlation and MI
class UnionFeatureSelector(BaseEstimator, TransformerMixin):
    """
    Fits MIRegSelector and CorrSelector, returns the union of their selected columns.
    Order rule: MI order first, then Corr-only in Corr order.
    """
    def __init__(self, mi_k=40, mi_neighbors=5, mi_random_state=42,
                 corr_k=40, corr_method='pearson', corr_drop_collinear=True, corr_threshold=0.92):
        self.mi_k = mi_k; self.mi_neighbors = mi_neighbors; self.mi_random_state = mi_random_state
        self.corr_k = corr_k; self.corr_method = corr_method
        self.corr_drop_collinear = corr_drop_collinear; self.corr_threshold = corr_threshold
        self.mi_ = None; self.corr_ = None
        self.union_columns_ = None

    def fit(self, X, y):
        X = pd.DataFrame(X); y = pd.Series(y).astype(float)

        self.mi_ = MIRegSelector(k=self.mi_k, n_neighbors=self.mi_neighbors,
                                 random_state=self.mi_random_state).fit(X, y)
        self.corr_ = CorrSelector(k=self.corr_k, method=self.corr_method,
                                  drop_collinear=self.corr_drop_collinear,
                                  collinear_threshold=self.corr_threshold).fit(X, y)

        mi_list = list(self.mi_.get_feature_names_out())
        co_list = list(self.corr_.get_feature_names_out())

        seen = set()
        ordered_union = []
        # MI-ranked first
        for f in mi_list:
            if f not in seen:
                ordered_union.append(f); seen.add(f)
        # then Corr-ranked if not already included
        for f in co_list:
            if f not in seen:
                ordered_union.append(f); seen.add(f)

        self.union_columns_ = ordered_union
        return self

    def transform(self, X):
        X = pd.DataFrame(X)
        return X[self.union_columns_]

    def get_feature_names_out(self, input_features=None):
        return np.array(self.union_columns_)
    
    #to combine the pipeline as rows dropped need to be aligned first before further preprocessing
class PreprocessBundle(BaseEstimator, TransformerMixin):
    """
    1) row_ops.fit_transform(X) may drop rows, that's why we will use its output index to align y
    2) preprocess.fit_transform(X_rows, y_rows) must not drop rows
    """
    def __init__(self, row_ops, preprocess):
        self.row_ops = row_ops
        self.preprocess = preprocess

    def fit_transform(self, X, y):
        X_rows = self.row_ops.fit_transform(X)
        y_rows = pd.Series(y).loc[X_rows.index]
        X_final = self.preprocess.fit_transform(X_rows, y_rows)
        return X_final, y_rows

    def transform(self, X, y=None, require_y=False):
        X_rows = self.row_ops.transform(X)
        X_final = self.preprocess.transform(X_rows)
        if y is None:
            if require_y:
                raise ValueError("y is required for alignment but was None.")
            return X_final
        y_rows = pd.Series(y).loc[X_rows.index]
        if len(X_final) != len(y_rows):
            raise ValueError("Post-transform X and y lengths differ after alignment.")
        return X_final, y_rows

    def fit(self, X, y=None):
        self.fit_transform(X, y)
        return self

    def get_feature_names_out(self):
        if hasattr(self.preprocess, "get_feature_names_out"):
            return list(self.preprocess.get_feature_names_out())
        if hasattr(self.preprocess, "named_steps") and "select_union" in self.preprocess.named_steps:
            return list(self.preprocess.named_steps["select_union"].get_feature_names_out())
        raise AttributeError("final_preprocess cannot produce feature names.")