from typing import Iterable, Literal, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def season_plot(
    df: pd.DataFrame,
    period: Literal["quarter", "month", "week", "day"],
    value_col: str,
    hue: Optional[str] = None,
    palette: Optional[str] = "viridis",
    add_mean_line: bool = False,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Creates a seasonal plot by overlaying all instances of the specified period.

    Args:
        df : pd.DataFrame
            The DataFrame containing the time series data, with the time column as the index.
        period : {'quarter', 'month', 'week', 'day'}
            The period over which to plot seasonality.
        value_col : str
            The column name containing the values to be plotted (e.g., temperature, sales, etc.).
        palette : str, optional
            The color palette to use for the lines. Default is 'viridis'.
        add_mean_line : bool, optional
            Whether to add a line representing the mean of the values for each season. Default is False.

    """
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("The DataFrame must have a DatetimeIndex as its index.")

    match period:
        case "quarter":
            df["Season"] = df.index.quarter
            x_label = "Quarter"
            x_tick_labels = ["Q1", "Q2", "Q3", "Q4"]
        case "month":
            df["Season"] = df.index.month
            x_label = "Month"
            x_tick_labels = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        case "week":
            df["Season"] = df.index.isocalendar().week
            x_label = "Week"
            x_tick_labels = [f"W{w}" for w in range(1, 53)]
        case "day":
            df["Season"] = df.index.weekday + 1  # 1 = Monday, ..., 7 = Sunday
            x_label = "Day"
            x_tick_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        case _:
            raise ValueError(
                "Unsupported period. Choose from 'quarter', 'month', 'week', or 'day'."
            )

    # Create the plot using sns.lineplot
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.lineplot(
        data=df,
        x="Season",
        y=value_col,
        hue=hue or "Season",
        palette=palette,
        ax=ax,
        alpha=0.7,
    )
    sns.despine()

    # Add mean line if specified
    if add_mean_line:
        mean_values = df.groupby("Season")[value_col].mean().reset_index()
        ax.plot(
            mean_values["Season"],
            mean_values[value_col],
            color="red",
            linestyle="--",
            linewidth=1.5,
        )

    # Set labels and ticks
    ax.set_xlabel(x_label)
    ax.set_ylabel(value_col)
    if x_tick_labels is not None:
        ax.set_xticks(range(1, len(x_tick_labels) + 1))
        ax.set_xticklabels(x_tick_labels, rotation=45)

    return fig, ax


def subseries_plot(
    df: pd.DataFrame,
    period: Literal["quarter", "month", "week", "day"],
    value_col: str,
    x_col: Literal["year"] | str = "year",
    hue_col: Optional[str] = None,
    add_mean_line: bool = False,
    palette: Optional[str] = "viridis",
    col_wrap: Optional[int] = None,
) -> sns.FacetGrid:
    """
    Creates a subseries plot using Seaborn based on the specified period using sns.FacetGrid.

    Args:
        df : pd.DataFrame
            The DataFrame containing the time series data, with the time column as the index.
        period : {'quarter', 'month', 'week', 'day'}
            The period over which to plot the subseries.
        value_col : str
            The column name containing the values to be plotted.
        x_col : {'year', 'month'}, optional
            The column to use for the x-axis. Default is 'year'.
        hue_col : str, optional
            The column to use for the hue in the plot. Default is None.
        palette : str, optional
            The color palette to use for the plots. Default is 'viridis'.
        col_wrap : int, optional
            The number of columns to use in the FacetGrid. Default is None -> single row.
        add_mean_line : bool, optional
            Whether to add a mean line to each subplot. Default is False.

    Returns:
        sns.FacetGrid
            A Seaborn FacetGrid object containing the plot.
    """
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("The DataFrame must have a DatetimeIndex as its index.")

    match x_col:
        case "year":
            if "year" not in df.columns:
                df["year"] = df.index.year
        case _:
            assert x_col in df.columns, f"{x_col} not in DataFrame columns."

    # Group based on specified period
    match period:
        case "month":
            df["SubPeriod"] = df.index.strftime(
                "%b"
            )  # Abbreviated month names (Jan, Feb, ...)
        case "week":
            df["SubPeriod"] = df.index.strftime("W%U")  # Week numbers (W01, W02, ...)
        case "quarter":
            df["SubPeriod"] = df.index.to_period("Q").strftime(
                "Q%q"
            )  # Quarter format (Q1, Q2, ...)
        case "day":
            df["SubPeriod"] = df.index.strftime(
                "%a"
            )  # Abbreviated day names (Mon, Tue, ...)
        case _:
            raise ValueError(
                "Unsupported period. Choose from 'quarter', 'month', 'week', or 'day'."
            )

    # Create the FacetGrid for the subseries plot
    g = sns.FacetGrid(
        df,
        col="SubPeriod",
        col_wrap=col_wrap,
        hue=hue_col,
        sharey=True,
        height=4,
        palette=palette,
    )
    g.map_dataframe(sns.lineplot, x=x_col, y=value_col)

    # Add mean line to each subplot
    if add_mean_line:
        for ax in g.axes.flat:
            subperiod = ax.get_title().split("=")[1].strip()
            mean_value = df[df["SubPeriod"] == subperiod][value_col].mean()
            ax.axhline(mean_value, ls="--", color="red", label="Mean")

    # Add legens, labels and titles
    if hue_col is not None:
        g.add_legend(title=hue_col)
        g._legend.set_bbox_to_anchor((1, 0.5))

    g.set_titles(col_template="{col_name}")
    g.set_axis_labels(x_col, value_col)
    for ax in g.axes.flat:
        plt.setp(ax.get_xticklabels(), rotation=45)

    return g


def lag_plot(
    df: pd.DataFrame,
    value_column: str,
    lags: Iterable[int],
    col_wrap: int = 4,
) -> sns.FacetGrid:
    """
    Creates lag plots for a time series using the specified lags, with a superimposed KDE.

    Args:
        df : pd.DataFrame
            The DataFrame containing the time series data, with the time column as the index.
        value_column : str
            The column name containing the values to be plotted.
        lags : Iterable[int]
            Iterable of lags to create the lag plots for (e.g., [1, 2, 3]).
        col_wrap : int, optional
            The number of columns to wrap the plots into. Default is 4.
        palette : str, optional
            The color palette to use for the KDE. Default is 'coolwarm'.

    Returns:
        sns.FacetGrid
            A Seaborn FacetGrid object containing the lag plots.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("The DataFrame must have a DatetimeIndex as its index.")

    # Compute lags values
    lagged_data = dict(
        map((lambda k: (f"{value_column}(t-{k})", df[value_column].shift(k))), lags)
    )
    lagged_data[value_column] = df[value_column]
    lag_df = pd.DataFrame(lagged_data)
    lag_df = lag_df.dropna().melt(
        id_vars=value_column, var_name="Lag", value_name="Lagged Value"
    )  # melt: wide -> long

    # Create FacetGrid
    g = sns.FacetGrid(
        lag_df, col="Lag", col_wrap=col_wrap, height=4, sharex=False, sharey=False
    )
    g.map_dataframe(sns.scatterplot, x="Lagged Value", y=value_column, color="black")
    g.map_dataframe(
        sns.kdeplot,
        x="Lagged Value",
        y=value_column,
        fill=True,
        levels=5,
        alpha=0.5,
        cmap="coolwarm",
    )

    # Adjust color intensity, reverse it to match high density = red
    for ax in g.axes.flat:
        ax.collections[1].set_alpha(0.3)

    g.set_axis_labels("Lagged Value", f"{value_column}(t)")
    g.set_titles(col_template="{col_name}")

    plt.tight_layout()
    return g
