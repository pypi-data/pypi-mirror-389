import unittest
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import time

from test.resources import logger

from raspberry_wifi_scanner.data_collection import scan
from raspberry_wifi_scanner.dataframe_functions import split_by_band

from raspberry_wifi_scanner.plotting import (
    gaussian_curve,
    plot_curves,
    plot_over_time,
)


class TestPlotting(unittest.TestCase):
    """Defines a class to test functions from within the plotting module
    (assumes test runs on machine with at least one valid wireless interface that supports scanning)"""

    def test_gaussian_curve(self):
        """Assert that gaussian_curve() returns arrays with values in the correct range"""
        center_channels = [number for number in range(1, 12)]  # 1 -> 11
        signal_quality = [quality / 10 for quality in range(1, 11)]  # 0.1 -> 1.0
        spread_range = [number for number in range(1, 6)]  # 1 -> 5

        for channel in center_channels:
            logger.debug(f"Checking center channel: {channel}")
            for quality in signal_quality:
                logger.debug(f"Checking signal quality: {quality}")
                for spread in spread_range:
                    logger.debug(f"Checking spread: {spread}")

                    x, y = gaussian_curve(
                        center=channel, quality=quality, spread=spread
                    )
                    self.assertIsInstance(x, np.ndarray)
                    self.assertIsInstance(y, np.ndarray)

                    self.assertEqual(len(x), len(y), "Arrays are not of equal length")

                    leftmost_channel = channel - spread
                    rightmost_channel = channel + spread

                    # Approximations to account for some variation
                    self.assertEqual(leftmost_channel, round(x[0]))
                    self.assertEqual(rightmost_channel, round(x[-1]))

                    middle_y_index = round(len(y) / 2)
                    middle_y_value = round(y[middle_y_index], 1)
                    self.assertEqual(quality, middle_y_value)

    def test_plot_curves(self):
        """Assert plot_curves() returns a valid go.Figure"""
        main_df = scan()
        two_gig, five_gig = split_by_band(main_df)

        two = plot_curves(two_gig, "2")
        five = plot_curves(five_gig, "5")

        for figure in [two, five]:
            self.assertIsInstance(figure, go.Figure)

    def test_plot_over_time(self):
        """Assert plot_over_time() returns a valid go.Figure"""
        df_one = scan()
        time.sleep(1)
        df_two = scan()

        df = pd.concat([df_one, df_two])

        grouped = (
            df.groupby(["time", "channel"])["channel"].value_counts().reset_index()
        )

        fig = plot_over_time(
            df=grouped, y_column="count", category="channel", title="Test Plot"
        )

        self.assertIsInstance(fig, go.Figure)
