from typing import Literal, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def season_plot(
    df: pd.DataFrame,
    period: Literal["quarter", "month", "week", "day"],
    value_column: str,
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
        value_column : str
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
            x_label = "Day of Week"
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
        y=value_column,
        hue=hue or "Season",
        palette=palette,
        ax=ax,
        alpha=0.7,
    )
    sns.despine()

    # Add mean line if specified
    if add_mean_line:
        mean_values = df.groupby("Season")[value_column].mean().reset_index()
        ax.plot(
            mean_values["Season"],
            mean_values[value_column],
            color="red",
            linestyle="--",
            linewidth=1.5,
        )

    # Set labels and ticks
    ax.set_xlabel(x_label)
    ax.set_ylabel(value_column)
    if x_tick_labels is not None:
        ax.set_xticks(range(1, len(x_tick_labels) + 1))
        ax.set_xticklabels(x_tick_labels, rotation=45)

    return fig, ax


def subseries_plot(
    df: pd.DataFrame,
    period: Literal["quarter", "month", "week", "day"],
    value_column: str,
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
        value_column : str
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
    g.map_dataframe(sns.lineplot, x=x_col, y=value_column)

    # Add mean line to each subplot
    if add_mean_line:
        for ax in g.axes.flat:
            subperiod = ax.get_title().split("=")[1].strip()
            mean_value = df[df["SubPeriod"] == subperiod][value_column].mean()
            ax.axhline(mean_value, ls="--", color="red", label="Mean")

    # Add legens, labels and titles
    if hue_col is not None:
        g.add_legend(title=hue_col)
        g._legend.set_bbox_to_anchor((1, 0.5))

    g.set_titles(col_template="{col_name}")
    g.set_axis_labels(x_col, value_column)
    for ax in g.axes.flat:
        plt.setp(ax.get_xticklabels(), rotation=45)

    return g
