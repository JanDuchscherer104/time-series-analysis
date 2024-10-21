
# Time Series Analysis Helpers

## Installation

```python
pip install -e tsa_helpers
```

## Current Features

### `season_plot`

The `season_plot` function creates a seasonal plot by overlaying all instances of the specified period.

- **Parameters:**
  - `df` (pd.DataFrame): The DataFrame containing the time series data, with the time column as the index.
  - `period` (Literal["quarter", "month", "week", "day"]): The period over which to plot seasonality.
  - `value_column` (str): The column name containing the values to be plotted (e.g., temperature, sales, etc.).
  - `hue` (Optional[str], default=None): The column name to use for color encoding.
  - `palette` (Optional[str], default="viridis"): The color palette to use for the lines.
  - `add_mean_line` (bool, default=False): Whether to add a line representing the mean of the values for each season.

- **Returns:**
  - `Tuple[plt.Figure, plt.Axes]`: The figure and axes objects of the plot.

### `subseries_plot`

The `subseries_plot` function creates a subseries plot using Seaborn based on the specified period using `sns.FacetGrid`.

- **Parameters:**
  - `df` (pd.DataFrame): The DataFrame containing the time series data, with the time column as the index.
  - `period` (Literal["quarter", "month", "week", "day"]): The period over which to plot the subseries.
  - `value_column` (str): The column name containing the values to be plotted.
  - `x_col` (Literal["year"] | str, default="year"): The column to use for the x-axis.
  - `hue_col` (Optional[str], default=None): The column to use for the hue in the plot.
  - `palette` (Optional[str], default="viridis"): The color palette to use for the plots.
  - `col_wrap` (Optional[int], default=None): The number of columns to use in the FacetGrid.
  - `add_mean_line` (bool, default=False): Whether to add a mean line to each subplot.

- **Returns:**
  - `sns.FacetGrid`: A Seaborn FacetGrid object containing the plot.

### `lag_plot`

The `lag_plot` function creates lag plots for a time series using the specified lags, with a superimposed KDE.

- **Parameters:**
  - `df` (pd.DataFrame): The DataFrame containing the time series data, with the time column as the index.
  - `value_column` (str): The column name containing the values to be plotted.
  - `lags` (Iterable[int]): Iterable of lags to create the lag plots for (e.g., [1, 2, 3]).
  - `col_wrap` (int, default=4): The number of columns to wrap the plots into.

- **Returns:**
  - `sns.FacetGrid`: A Seaborn FacetGrid object containing the lag plots.
