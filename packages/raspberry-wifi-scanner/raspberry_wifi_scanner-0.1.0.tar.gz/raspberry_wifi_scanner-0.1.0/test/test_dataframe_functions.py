import unittest
import pandas as pd

from test.resources import logger

from raspberry_wifi_scanner.data_collection import scan

from raspberry_wifi_scanner.dataframe_functions import (
    split_by_band,
    split_by_mac_list,
    dbm_per_channel,
)

from raspberry_wifi_scanner.definitions import two_gigahertz_channels


data = {
    "time": [1, 2, 3, 4],
    "mac": [
        "11:11:11:11:11:11",
        "22:22:22:22:22:22",
        "00:00:00:00:00:00",
        "33:33:33:33:33:33",
    ],
    "essid": ["a", "b", "c", "d"],
    "channel": [11, 1, 149, 36],
    "frequency_GHz": [2.462, 2.412, 5.745, 5.180],
    "signal_dBm": [-78, -59, -43, -43],
    "quality": ["32/70", "51/70", "67/70", "67/70"],
    "quality_decimal": [0.457143, 0.728571, 0.957143, 0.957143],
}

df_data = pd.DataFrame(data)


class TestDataFrameFunctions(unittest.TestCase):
    """Defines a class to test functions from within the dataframe_functions module
    (assumes test runs on machine with at least one valid wireless interface that supports scanning)"""

    def test_split_by_band(self):
        """Assert that split_by_band() produces two separate Dataframes containing the expected channels"""
        df = scan()

        two, five = split_by_band(df)

        two_channels = two["channel"].unique()
        logger.debug(f"Channels found in the 2.4 GHz dataframe: {two_channels}")
        five_channels = five["channel"].unique()
        logger.debug(f"Channels found in the 5/6 GHz dataframe: {five_channels}")

        for channel in two_channels:
            self.assertTrue(channel in two_gigahertz_channels)

        for channel in five_channels:
            self.assertTrue(channel not in two_gigahertz_channels)

    def test_split_by_mac_list(self):
        """Assert that split_by_mac_list() returns the mac addresses in the correct dataframes"""

        macs_to_include = ["00:00:00:00:00:00", "11:11:11:11:11:11"]
        logger.debug(f"Macs to include: {macs_to_include}")

        my_macs, not_my_macs = split_by_mac_list(df_data, macs_to_include)

        logger.debug(f"Macs in include df: {my_macs['mac'].unique()}")
        for mac in my_macs["mac"].unique():
            self.assertTrue(mac in macs_to_include)

        logger.debug(f"Macs in exclude df: {not_my_macs['mac'].unique()}")
        for mac in not_my_macs["mac"].unique():
            self.assertTrue(mac not in macs_to_include)

    def test_dbm_per_channel(self):
        """Assert that dbm_per_channel() returns a df with the correct columns"""
        dbm_data = {
            "channel": [1, 2, 7, 8, 9, 11],
            "signal_dBm": [-58, -90, -43, -51, -67, -62],
        }

        dbm_df = pd.DataFrame(dbm_data)

        expected_columns = ["channel", "overall_dBm", "power_mW"]

        no_overlap_calcs = dbm_per_channel(
            df=dbm_df, valid_channels=two_gigahertz_channels, overlap=False
        )
        # Non overlapping calculations should include only the original channels
        self.assertEqual(
            sorted(dbm_data.get("channel")),
            sorted(no_overlap_calcs["channel"].tolist()),
        )

        overlap_calcs = dbm_per_channel(
            df=dbm_df, valid_channels=two_gigahertz_channels, overlap=True
        )
        self.assertEqual(
            sorted(two_gigahertz_channels), sorted(overlap_calcs["channel"].tolist())
        )

        # In either case, the same columns should be present
        for df in [no_overlap_calcs, overlap_calcs]:
            self.assertEqual(sorted(expected_columns), sorted(df.columns))
