import funcy
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion

from dengue_prediction.util import get_arr_desc


class NoFitMixin:
    def fit(self, X, y=None, **fit_kwargs):
        return self


class SimpleFunctionTransformer(BaseEstimator, NoFitMixin, TransformerMixin):
    def __init__(self, func):
        super().__init__()
        self.func = func

    def transform(self, X, **transform_kwargs):
        return self.func(X)


class IdentityTransformer(SimpleFunctionTransformer):
    def __init__(self):
        super().__init__(funcy.identity)


class GroupedFunctionTransformer(BaseEstimator, NoFitMixin, TransformerMixin):
    def __init__(self, func, groupby_kwargs=None, func_args=None,
                 func_kwargs=None):
        super().__init__()
        self.func = func
        self.func_args = func_args if func_args else ()
        self.func_kwargs = func_kwargs if func_kwargs else {}
        self.groupby_kwargs = groupby_kwargs if groupby_kwargs else {}

    def transform(self, X, **transform_kwargs):
        if self.groupby_kwargs:
            call = X.sort_index().groupby(**self.groupby_kwargs).apply
        else:
            call = X.sort_index().pipe
        return call(self.func, *self.func_args, **self.func_kwargs)


class DelegatingTransformerMixin(TransformerMixin):
    # TODO remove? almost certainly this can be accomplished with inheritance
    # directly
    def fit(self, X, y=None, **fit_args):
        return self._transformer.fit(X, y=None, **fit_args)

    def transform(self, X, **transform_args):
        return self._transformer.transform(X, **transform_args)


class SingleLagger(GroupedFunctionTransformer):
    def __init__(self, lag, groupby_kwargs=None):
        super().__init__(lambda x: x.shift(lag), groupby_kwargs=groupby_kwargs)


def make_multi_lagger(lags, groupby_kwargs=None):
    laggers = [SingleLagger(l, groupby_kwargs=groupby_kwargs) for l in lags]
    feature_union = FeatureUnion([
        (repr(lagger), lagger) for lagger in laggers
    ])
    return feature_union


class LagImputer(GroupedFunctionTransformer):
    def __init__(self, groupby_kwargs=None):
        super().__init__(lambda x: x.fillna(method='ffill'),
                         groupby_kwargs=groupby_kwargs)


class ValueReplacer(BaseEstimator, NoFitMixin, TransformerMixin):
    def __init__(self, value='NaN', replacement=0.0):
        super().__init__()
        self.value = value
        self.replacement = replacement

    def transform(self, X, **transform_kwargs):
        X = X.copy()
        if self.value != 'NaN':
            mask = X == self.value
        else:
            mask = np.isnan(X)
        X[mask] = self.replacement
        return X


class NullFiller(BaseEstimator, NoFitMixin, TransformerMixin):
    def __init__(self, replacement=0.0):
        super().__init__()
        self.replacement = replacement

    def transform(self, X, **transform_kwargs):
        X = X.copy()
        mask = np.isnan(X)
        X[mask] = self.replacement
        return X


class NullIndicator(BaseEstimator, NoFitMixin, TransformerMixin):
    def transform(self, X, **tranform_kwargs):
        return np.isnan(X).astype(int)


class NamedFramer(BaseEstimator, NoFitMixin, TransformerMixin):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def transform(self, X, **transform_kwargs):
        if isinstance(X, pd.Index):
            return X.to_series().to_frame(name=self.name)
        elif isinstance(X, pd.Series):
            return X.to_frame(name=self.name)
        elif isinstance(X, np.ndarray):
            if X.ndim == 1:
                return pd.DataFrame(data=X.reshape(1, -1), columns=[self.name])
            elif X.ndim == 2 and X.shape[1] == 1:
                return pd.DataFrame(data=X, columns=[self.name])

        raise TypeError(
            "Couldn't convert object {} to named 1d DataFrame.".format(
                get_arr_desc(X)))
