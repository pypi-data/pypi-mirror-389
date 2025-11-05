import numpy as np
import pandas as pd
import plotly.graph_objects as go


def gaussian_curve(
    center: int, quality: float, spread: int = 2, step: float = 0.1
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return a tuple of ndarray (x,y) for plotting approximate curves

    :param center: channel at which network is centered
    :type center: int

    :param quality: signal quality of the network (typically between 0 and 1)
    :type quality: float

    :param spread: number of channels for the curve to reach on either side of center (typically around 2 for 20 MHz width)
    :type spread: int

    :param step: increments on the x-axis to calculate, typically a smaller number will produce a smoother curve
    :type step: float

    :return: two arrays of x, y values for plotting
    :rtype: tuple[np.ndarray, np.ndarray]

    """
    x: np.ndarray = np.arange(center - spread, center + spread + step, step)
    sigma: float = 0.8
    y: np.ndarray = quality * np.exp(-((x - center) ** 2) / (2 * sigma**2))
    return x, y


def plot_curves(df: pd.DataFrame, title: str, spread: int = 2) -> go.Figure:
    """
    Return a Plotly Figure of plotted curves based on signal_quality column and defined channel spread

    :param df: Dataframe containing signal quality and channel columns along with essid for its name
    :type df: pd.DataFrame

    :param title: Title of plot
    :type title: str

    :param spread: number of channels on left/right side of center to cover
    :type spread: int

    :return: Figure with a curve for every supplied row/network
    :rtype: go.Figure
    """
    curves: list[go.Scatter] = []

    for _, network in df.iterrows():
        x: np.ndarray
        y: np.ndarray

        x, y = gaussian_curve(
            center=network["channel"], quality=network["quality_decimal"], spread=spread
        )
        curve: go.Scatter = go.Scatter(x=x, y=y, mode="lines", name=network["essid"])
        curves.append(curve)

    layout: go.Layout = go.Layout(
        title=title,
        xaxis=dict(title="Wi-Fi Channel", dtick=1),
        yaxis=dict(title="Signal Quality", range=[0, 1.1]),
    )

    fig: go.Figure = go.Figure(data=curves, layout=layout)

    return fig


def plot_over_time(
    df: pd.DataFrame, y_column: str, category: str, title: str
) -> go.Figure:
    """
    Return a figure of a given column plotted over time based on a given category

    :param df: Aggregated/sorted DataFrame recommend to sort_values(by=['time', category]) in advance
    :type df: pd.DataFrame

    :param y_column: Given column to plot on the Y-Axis
    :type y_column: str

    :param category: column name to separate the data into groups for individual traces, examples: "channel", "mac", "essid", etc
    :type category: str

    :param title: Title for the plot
    :type title: str

    :return: A figure with a trace for each unique value in the category column
    :rtype: go.Figure
    """
    fig: go.Figure = go.Figure()

    for cat in df[category].unique():
        cat_df: pd.DataFrame = df[df[category] == cat].reset_index()
        fig.add_trace(
            go.Scatter(
                x=cat_df["time"], y=cat_df[y_column], mode="lines", name=f"{cat}"
            )
        )

    fig.update_layout(title=title)

    return fig
