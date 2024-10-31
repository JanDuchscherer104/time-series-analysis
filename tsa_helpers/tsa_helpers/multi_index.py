from concurrent.futures import ThreadPoolExecutor
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Self,
    Tuple,
    TypeVar,
    Union,
    overload,
)

import pandas as pd
import seaborn as sns
from darts import TimeSeries
from darts.models.forecasting.forecasting_model import ForecastingModel
from matplotlib import pyplot as plt
from pandas import DataFrame, Series

T = TypeVar("T")


class MITimeSeries:
    """
    MITimeSeries is a container for multiple TimeSeries objects, each identified by a unique multi-key.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        key_col: Union[str, List[str]],
        value_cols: Optional[Union[List[str], str]] = None,
        fill_missing_dates: Optional[bool] = False,
        freq: Optional[Union[str, int]] = None,
        fillna_value: Optional[float] = None,
        static_covariates: Optional[Union[Series, DataFrame]] = None,
        hierarchy: Optional[Dict] = None,
        is_parallel: Optional[bool] = False,
    ) -> None:
        """
        Initialize a multi-indexed TimeSeries object.

        Parameters:
            df (pd.DataFrame): The DataFrame containing time series data.
            key_col (Union[str, List[str]]): The column(s) to use as the key for grouping.
            value_col (Optional[str]): The column name for the value.
            is_parallel (Optional[bool]): Whether to perform operations in parallel.
        """
        self.__key_col = key_col
        self.__value_col = value_cols
        self.is_parallel = is_parallel
        self.series_groups: Dict[Tuple, TimeSeries] = self.convert_to_timeseries(
            df,
            key_col,
            value_cols,
            fill_missing_dates,
            freq,
            fillna_value,
            static_covariates,
            hierarchy,
            self.is_parallel,
        )

    @staticmethod
    def convert_to_timeseries(
        df: pd.DataFrame,
        key_col: Union[str, List[str]],
        value_cols: Optional[Union[List[str], str]] = None,
        fill_missing_dates: Optional[bool] = False,
        freq: Optional[Union[str, int]] = None,
        fillna_value: Optional[float] = None,
        static_covariates: Optional[Union[Series, DataFrame]] = None,
        hierarchy: Optional[Dict] = None,
        is_parallel: Optional[bool] = False,
    ) -> Dict[Tuple, TimeSeries]:
        """
        Convert a DataFrame into a dictionary of TimeSeries objects.

        Parameters:
            df (pd.DataFrame): The DataFrame containing time series data.
            key_col (Union[str, List[str]]): The column(s) to use as the key for grouping.
            value_col (Optional[str]): The column name for the value.
            is_parallel (Optional[bool]): Whether to perform operations in parallel.

        Returns:
            Dict[Tuple, TimeSeries]: A dictionary mapping keys to TimeSeries objects.
        """
        if isinstance(key_col, str):
            key_col = [key_col]
        grouped = df.groupby(key_col)
        timeseries_dict = {}

        def create_timeseries(name_group):
            name, group = name_group
            key = name if isinstance(name, tuple) else (name,)
            ts = TimeSeries.from_dataframe(
                df=group,
                value_cols=value_cols,
                freq=freq,
                fill_missing_dates=fill_missing_dates,
                fillna_value=fillna_value,
                static_covariates=static_covariates,
                hierarchy=hierarchy,
            )
            return key, ts

        if is_parallel:
            with ThreadPoolExecutor() as executor:
                for key, ts in executor.map(create_timeseries, grouped):
                    timeseries_dict[key] = ts
        else:
            for key, group in grouped:
                key, ts = create_timeseries((key, group))
                timeseries_dict[key] = ts

        return timeseries_dict

    @overload
    def __getitem__(self, key: str) -> TimeSeries: ...

    @overload
    def __getitem__(self, key: Tuple) -> TimeSeries: ...

    @overload
    def __getitem__(self, key: slice) -> "MITimeSeries": ...

    @overload
    def __getitem__(self, key: List[str]) -> "MITimeSeries": ...

    def __getitem__(
        self, key: Union[str, Tuple, slice, List]
    ) -> Union[TimeSeries, "MITimeSeries"]:
        """
        Retrieve a TimeSeries object or a subset of MITimeSeries by key.

        Parameters:
            key (Union[str, Tuple, slice, List]): The key(s) identifying the TimeSeries.

        Returns:
            Union[TimeSeries, MITimeSeries]: The corresponding TimeSeries object(s).
        """
        if isinstance(key, (str, int)):
            key = (key,)
        elif isinstance(key, list):
            sub_series = {
                k: self.series_groups[k] for k in self.series_groups if k[0] in key
            }
            if not sub_series:
                raise KeyError(f"No TimeSeries found for keys: {key}")
            return self.from_series_dict(sub_series, self.__key_col, self.__value_col)
        elif isinstance(key, slice):
            all_keys = sorted(set(k[0] for k in self.series_groups))
            sliced_keys = all_keys[key]
            sub_series = {
                k: self.series_groups[k]
                for k in self.series_groups
                if k[0] in sliced_keys
            }
            return self.from_series_dict(sub_series, self.__key_col, self.__value_col)
        elif not isinstance(key, tuple):
            raise TypeError("Invalid key type.")

        if key in self.series_groups:
            return self.series_groups[key]

        raise KeyError(f"No TimeSeries found for key: {key}")

    def __setitem__(self, key: Union[str, Tuple], value: TimeSeries) -> None:
        """
        Set a TimeSeries object for a given key.

        Parameters:
            key (Union[str, Tuple]): The key identifying the TimeSeries.
            value (TimeSeries): The TimeSeries object to set.
        """
        if isinstance(key, (str, int)):
            key = (key,)
        if not isinstance(value, TimeSeries):
            raise ValueError("Value must be a darts TimeSeries object.")
        self.series_groups[key] = value

    @classmethod
    def from_series_dict(
        cls,
        series_dict: Dict[Tuple, TimeSeries],
        key_col: Union[str, List[str]],
        value_cols: Optional[Union[List[str], str]] = None,
    ) -> "MITimeSeries":
        """
        Create an MITimeSeries from a dictionary of TimeSeries objects.

        Parameters:
            series_dict (Dict[Tuple, TimeSeries]): The dictionary of TimeSeries objects.
            key_col (Union[str, List[str]]): The key column(s).
            value_col (Optional[str]): The value column name.

        Returns:
            MITimeSeries: The new MITimeSeries object.
        """
        mi_series = cls.__new__(cls)
        mi_series.__key_col = key_col
        mi_series.__value_col = value_cols
        mi_series.series_groups = series_dict
        mi_series.is_parallel = False
        return mi_series

    @overload
    def apply(
        self, fn: Callable[[TimeSeries], TimeSeries], *args, **kwargs
    ) -> "MITimeSeries": ...

    @overload
    def apply(
        self, fn: Callable[[TimeSeries], T], *args, **kwargs
    ) -> Dict[Tuple, T]: ...

    def apply(
        self, fn: Callable[[TimeSeries], Any], *args, **kwargs
    ) -> Union[Dict, "MITimeSeries"]:
        """
        Apply a function to each TimeSeries in the MITimeSeries.
        Returns MITimeSeries if results are TimeSeries objects, otherwise returns dict.

        Parameters:
            fn: Function to apply to each TimeSeries
            *args: Positional arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Union[MITimeSeries, Dict]: MITimeSeries if results are TimeSeries, Dict otherwise
        """
        if self.is_parallel:
            with ThreadPoolExecutor() as executor:
                new_series = executor.map(
                    lambda item: (item[0], fn(item[1], *args, **kwargs)),
                    self.series_groups.items(),
                )
                new_series_dict = dict(new_series)
        else:
            new_series_dict = dict(
                map(
                    lambda item: (item[0], fn(item[1], *args, **kwargs)),
                    self.series_groups.items(),
                )
            )

        # Return MITimeSeries if all results are TimeSeries objects
        if all(isinstance(v, TimeSeries) for v in new_series_dict.values()):
            return self.from_series_dict(
                series_dict=new_series_dict,
                key_col=self.__key_col,
                value_cols=self.__value_col,
            )

        return new_series_dict

    def filter(
        self, predicate: Callable[[TimeSeries], bool], *args, **kwargs
    ) -> "MITimeSeries":
        """
        Filter TimeSeries objects based on a predicate function.

        Parameters:
            predicate: Function that takes a TimeSeries and returns bool
            *args: Additional arguments for predicate
            **kwargs: Additional keyword arguments for predicate

        Returns:
            MITimeSeries: New MITimeSeries containing only series that satisfy predicate
        """

        def apply_filter(key_ts):
            key, ts = key_ts
            return key, predicate(ts, *args, **kwargs)

        # Apply predicate to all series
        if self.is_parallel:
            with ThreadPoolExecutor() as executor:
                results = executor.map(apply_filter, self.series_groups.items())
                filtered_dict = {
                    key: self.series_groups[key] for key, keep in results if keep
                }
        else:
            filtered_dict = dict(
                filter(
                    lambda item: predicate(item[1], *args, **kwargs),
                    self.series_groups.items(),
                )
            )

        # Create new MITimeSeries with filtered series
        return self.from_series_dict(
            series_dict=filtered_dict,
            key_col=self.__key_col,
            value_cols=self.__value_col,
        )

    def keys_list(self) -> List[Tuple]:
        """
        Get the list of keys.

        Returns:
            List[Tuple]: List of keys.
        """
        return list(self.series_groups.keys())

    def items_list(self) -> List[Tuple[Tuple, TimeSeries]]:
        """
        Get the list of (key, TimeSeries) pairs.

        Returns:
            List[Tuple[Tuple, TimeSeries]]: List of (key, TimeSeries) pairs.
        """
        return list(self.series_groups.items())

    def __len__(self) -> int:
        """
        Get the number of TimeSeries objects.

        Returns:
            int: Number of TimeSeries objects.
        """
        return len(self.series_groups)

    def __iter__(self) -> Iterator[Tuple]:
        """
        Iterate over the keys.
        """
        return iter(self.series_groups)

    def attach_and_fit(
        self, models: Union[Dict[str, ForecastingModel], ForecastingModel]
    ) -> Self:
        """
        Fit forecasting model(s) to all TimeSeries objects.

        Parameters:
            models: Single model or dictionary of named models to fit
        """
        from copy import deepcopy

        def fit_model(key_ts):
            key, ts = key_ts
            if isinstance(models, dict):
                fitted = {
                    model_name: deepcopy(model).fit(ts)
                    for model_name, model in models.items()
                }
                return key, fitted
            else:
                model = deepcopy(models).fit(ts)
                return key, model

        if self.is_parallel:
            with ThreadPoolExecutor() as executor:
                fitted_models = dict(
                    executor.map(fit_model, self.series_groups.items())
                )
        else:
            fitted_models = dict(map(fit_model, self.series_groups.items()))

        self.__models = fitted_models
        return self

    def predict(self, forecast_horizon: int) -> "MITimeSeries":
        """
        Predict the next forecast_horizon steps for all TimeSeries objects.

        Parameters:
            forecast_horizon (int): The number of steps to forecast.

        Returns:
            MITimeSeries: A new MITimeSeries object containing the predictions.
        """

        def predict_forecast(key_model):
            key, model = key_model

            # Handle dictionary of models case
            if isinstance(model, dict):
                # Create predictions for each model
                model_predictions = {
                    model_name: fitted_model.predict(forecast_horizon)
                    for model_name, fitted_model in model.items()
                }
                # Combine all model predictions into single TimeSeries
                combined_ts = None
                for model_name, pred in model_predictions.items():
                    pred_renamed = pred.pd_dataframe().add_prefix(f"{model_name}_")
                    if combined_ts is None:
                        combined_ts = TimeSeries.from_dataframe(pred_renamed)
                    else:
                        combined_ts = combined_ts.concatenate(
                            TimeSeries.from_dataframe(pred_renamed), axis=1
                        )
                return key, combined_ts
            else:
                # Single model case
                return key, model.predict(forecast_horizon)

        if self.is_parallel:
            with ThreadPoolExecutor() as executor:
                predictions = dict(
                    executor.map(predict_forecast, self.__models.items())
                )
        else:
            predictions = dict(map(predict_forecast, self.__models.items()))

        # Get all unique model names for value_cols
        if isinstance(next(iter(self.__models.values())), dict):
            model_names = list(next(iter(self.__models.values())).keys())
            value_cols = [f"{model}_pred_{self.__value_col}" for model in model_names]
        else:
            value_cols = f"pred_{self.__value_col}"  # type: ignore

        return self.from_series_dict(
            series_dict=predictions, key_col=self.__key_col, value_cols=value_cols
        )

    def to_grouped_df(self) -> pd.DataFrame:
        """
        Convert MITimeSeries to a grouped DataFrame.

        Returns:
            pd.core.groupby.DataFrameGroupBy: DataFrame grouped by key_col(s)
        """
        grouped_df = self.to_df().groupby(
            self.__key_col if isinstance(self.__key_col, list) else [self.__key_col]
        )

        return grouped_df

    def to_df(self) -> pd.DataFrame:
        """
        Convert all contained TimeSeries to a single long-format DataFrame.

        Returns:
            pd.DataFrame: Long format DataFrame with key_col, time index and value_col(s).
        """

        def process_ts(key_ts):
            key, ts = key_ts
            ts_df = ts.pd_dataframe().reset_index()
            key_values = key if isinstance(key, tuple) else (key,)
            if isinstance(self.__key_col, list):
                for k_col, k_val in zip(self.__key_col, key_values):
                    ts_df[k_col] = k_val
            else:
                ts_df[self.__key_col] = key_values[0]
            return ts_df

        if self.is_parallel:
            with ThreadPoolExecutor() as executor:
                df_list = list(executor.map(process_ts, self.series_groups.items()))
        else:
            df_list = list(map(process_ts, self.series_groups.items()))

        combined_df = pd.concat(df_list, ignore_index=True)

        if isinstance(self.__value_col, list):
            id_vars = ["time"] + (
                self.__key_col if isinstance(self.__key_col, list) else [self.__key_col]
            )
            combined_df = combined_df.melt(
                id_vars=id_vars,
                value_vars=self.__value_col,
                var_name="variable",
                value_name="value",
            )

        return combined_df

    def plot(
        self,
        fig_size: Tuple[int, int] = (10, 6),
        value_col: Optional[str] = None,
        palette: Optional[
            Literal[
                "Set2",  # Distinct, colorblind-friendly
                "Dark2",  # High contrast, distinct
                "Paired",  # Good for categorical data
                "colorblind",  # Specifically designed for colorblindness
                "husl",  # Evenly spaced in HUSL color space
                "deep",  # Default seaborn palette
                "tab10",  # Tableau's categorical palette
                "bright",  # Vivid colors
            ]
        ] = "Set2",
        central_quantile: Optional[Union[float, str]] = 0.5,
        low_quantile: Optional[float] = 0.05,
        high_quantile: Optional[float] = 0.95,
        default_formatting: Optional[bool] = True,
        max_nr_components: Optional[int] = 10,
        ax: Optional[plt.Axes] = None,
        **kwargs,
    ) -> plt.Axes:
        """
        Plot all contained TimeSeries objects with different colors.

        Parameters:
            fig_size: Figure size (width, height)
            palette: Seaborn color palette name
            central_quantile: Central quantile for prediction intervals
            low_quantile: Lower quantile for prediction intervals
            high_quantile: Upper quantile for prediction intervals
            default_formatting: Use default plot formatting
            max_nr_components: Maximum number of components to plot
            ax: Matplotlib axes to plot on
            **kwargs: Additional arguments passed to plot

        Returns:
            plt.Axes: Matplotlib axes object
        """
        if ax is None:
            _, ax = plt.subplots(figsize=fig_size)

        n_colors = len(self.series_groups)
        colors = sns.color_palette(palette, n_colors=n_colors)
        linestyles = ["-", "--", ":", "-."]
        markers = [
            "o",
            "s",
            "^",
            "v",
            "D",
            "p",
            "h",
            "8",
            "*",
            "d",
        ]

        for i, (key, ts) in enumerate(self.series_groups.items()):
            if value_col is not None and ts.n_components > 1:
                if value_col not in ts.components:
                    raise ValueError(
                        f"Column '{value_col}' not found in components: {ts.components}"
                    )
                ts = ts[value_col]

            # Single component case
            if ts.n_components == 1:
                ts.plot(
                    label=f"{key}".strip(",()'"),
                    color=colors[i % len(colors)],
                    linestyle=linestyles[i % len(linestyles)],
                    central_quantile=central_quantile,
                    low_quantile=low_quantile,
                    high_quantile=high_quantile,
                    default_formatting=default_formatting,
                    max_nr_components=max_nr_components,
                    ax=ax,
                    **kwargs,
                )
            # Multiple components case
            else:
                for j, component in enumerate(ts.components):
                    ts[component].plot(
                        label=f"{str(key).strip(",()'")}_{component}",
                        color=colors[i % len(colors)],
                        linestyle=linestyles[i % len(linestyles)],
                        marker=markers[j % len(markers)],
                        markersize=5,
                        central_quantile=central_quantile,
                        low_quantile=low_quantile,
                        high_quantile=high_quantile,
                        default_formatting=default_formatting,
                        max_nr_components=max_nr_components,
                        ax=ax,
                        **kwargs,
                    )

        ax.set_ylabel(value_col or self.__value_col)
        ax.legend(bbox_to_anchor=(1.05, 1))
        plt.tight_layout()
        return ax

    def head(self, n: int = 5) -> pd.DataFrame:
        """
        Get the first n rows of the DataFrame.

        Parameters:
            n (int): The number of rows to return.

        Returns:
            pd.DataFrame: The first n rows of the DataFrame.
        """
        return self.to_df().head(n)

    def info(self, n: Optional[int] = None) -> None:
        """
        Display summary information about each TimeSeries in the collection.
        """
        from IPython.display import HTML, display

        summary_df = pd.DataFrame(
            [
                {
                    "Series": key[0],
                    "Time Range": f"{ts.start_time()} - {ts.end_time()}",
                    "Frequency": ts.freq_str or ts.freq,
                    "Points": len(ts),
                    "Missing": ts.pd_dataframe().isna().sum().sum(),
                    "Components": len(ts.components),
                    "Index Type": type(ts.time_index).__name__,
                }
                for key, ts in self.series_groups.items()
            ]
        )
        if n is not None:
            summary_df = summary_df.head(n)

        print(f"<class 'MITimeSeries'> with {len(self)} series\n")

        try:
            display(HTML(summary_df.to_html()))
        except:
            print(summary_df.to_string())
