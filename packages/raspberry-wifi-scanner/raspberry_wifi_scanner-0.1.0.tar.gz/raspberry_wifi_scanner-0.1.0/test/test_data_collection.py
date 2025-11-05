import unittest

import pandas.api.types as ptypes

from test.resources import logger

from raspberry_wifi_scanner.data_collection import (
    get_wireless_interfaces,
    iwlist_command,
    get_cells,
    parse_cells,
    generate_df_from_cells,
    scan,
    base_scan_columns,
)


class TestDataCollection(unittest.TestCase):
    """Defines a class to test functions from within the data_collection module
    (assumes test runs on machine with at least one valid wireless interface that supports scanning)
    """

    def test_get_wireless_interfaces(self):
        """Assert that get_wireless_interfaces() returns a valid list of interfaces represented as strings"""

        valid_interfaces = get_wireless_interfaces()
        logger.debug(f"Valid Interfaces: {valid_interfaces}")
        for interface in valid_interfaces:
            self.assertIsInstance(interface, str)

        invalid_path = "///invalid_path$$$$/."
        invalid_path_return = get_wireless_interfaces(invalid_path)
        self.assertTrue(invalid_path_return is None)

        path_without_interfaces = "/"
        no_interfaces = get_wireless_interfaces(path_without_interfaces)
        self.assertTrue(no_interfaces is None)

    def test_iwlist_command(self):
        """Assert that iwlist_command returns the expected text output"""

        invalid_interface_text = iwlist_command(interface="Invalid")
        logger.debug(f"Invalid interface text: {invalid_interface_text}")
        self.assertTrue("ERROR" in invalid_interface_text)

        valid_text_output = iwlist_command()
        logger.debug(f"Valid interface text: {valid_text_output}")
        self.assertTrue("Cell" in valid_text_output)

    def test_get_cells(self):
        """Assert that get cells returns an entry for each occurrence of 'Cell' and that each entry contains the correct keywords"""

        # Produce an empty list
        invalid_text = "This does not contain a network"
        self.assertEqual([], get_cells(invalid_text))

        occurrence_of_cell = iwlist_command().count("Cell")
        logger.debug(f"Cell occurs {occurrence_of_cell} times")

        cells = get_cells(iwlist_command())
        logger.debug(f"Cells: {cells}")

        # Account for all cells
        self.assertEqual(len(cells), occurrence_of_cell)

        expected_keywords = [
            "Address",
            "Channel",
            "Quality",
            "Signal level",
            "Encryption key",
            "ESSID",
        ]

        for cell in cells:
            logger.debug(f"Checking cell: {cell}")
            for keyword in expected_keywords:
                logger.debug(f"Checking keyword: {keyword}")
                self.assertTrue(keyword in cell, f"{keyword} not found in {cell}")

    def test_parse_cells(self):
        """Assert that parse_cells() returns a dictionary with the expected keys"""

        parsed_cells = parse_cells(get_cells(iwlist_command()))

        expected_keys = sorted(
            [
                "cell",
                "mac",
                "channel",
                "frequency_GHz",
                "frequency_info",
                "quality",
                "signal_dBm",
                "encryption_key",
                "essid",
                "remaining_info",
                "event_type",
            ]
        )

        for cell in parsed_cells:
            actual_keys = sorted(cell.keys())
            self.assertEqual(
                expected_keys,
                actual_keys,
                f"Expected keys: {expected_keys}, Actual keys: {actual_keys}",
            )

    def test_generate_df_from_cells(self):
        """Assert that generate_df_from_cells() returns a DataFrame with the correct columns, dtypes, and value ranges that make sense"""

        parsed_cells = parse_cells(get_cells(iwlist_command()))

        df = generate_df_from_cells(cells=parsed_cells)

        expected_columns = sorted(base_scan_columns)
        actual_columns = sorted(df.columns)

        logger.debug(
            f"Expected columns: {expected_columns}, Actual columns: {actual_columns}"
        )

        self.assertEqual(expected_columns, actual_columns)

        int_columns = ["channel", "signal_dBm"]
        float_columns = ["frequency_GHz", "quality_decimal"]
        datetime_columns = ["time"]

        non_string_columns = int_columns + float_columns + datetime_columns

        string_columns = [
            column for column in df.columns if column not in non_string_columns
        ]

        for column in int_columns:
            self.assertTrue(
                ptypes.is_integer_dtype(df[column]),
                f"Expected {column} to be an integer dtype",
            )

        for column in float_columns:
            self.assertTrue(
                ptypes.is_float_dtype(df[column]),
                f"Expected {column} to be a float dtype",
            )

        for column in datetime_columns:
            self.assertTrue(
                ptypes.is_datetime64_dtype(df[column]),
                f"Expected {column} to be a datetime dtype",
            )

        for column in string_columns:
            self.assertTrue(
                ptypes.is_string_dtype(df[column]),
                f"Expected {column} to be a string dtype",
            )

        # Quality_decimal
        self.assertTrue(df["quality_decimal"].max() <= 1.0)
        self.assertTrue(df["quality_decimal"].min() >= 0.0)

        # Signal dBm
        self.assertTrue(df["signal_dBm"].max() <= -30)
        self.assertTrue(df["signal_dBm"].min() >= -120)

        # Dataframe with a location
        location_df = generate_df_from_cells(cells=parsed_cells, location="Test")

        location_expected_columns = sorted(base_scan_columns + ["location"])
        location_actual_columns = sorted(location_df.columns)

        logger.debug(
            f"Expected columns: {location_expected_columns}, Actual columns: {location_actual_columns}"
        )

        self.assertEqual(location_expected_columns, location_actual_columns)

    def test_scan(self):
        """Assert that scan() returns a DataFrame with the correct columns, dtypes, and value ranges that make sense, empty if invalid interface"""
        invalid_interface_df = scan(interface="Invalid")
        self.assertTrue(invalid_interface_df.empty)

        df = scan()

        expected_columns = sorted(base_scan_columns)
        actual_columns = sorted(df.columns)

        logger.debug(
            f"Expected columns: {expected_columns}, Actual columns: {actual_columns}"
        )

        self.assertEqual(expected_columns, actual_columns)

        int_columns = ["channel", "signal_dBm"]
        float_columns = ["frequency_GHz", "quality_decimal"]
        datetime_columns = ["time"]

        non_string_columns = int_columns + float_columns + datetime_columns

        string_columns = [
            column for column in df.columns if column not in non_string_columns
        ]

        for column in int_columns:
            self.assertTrue(
                ptypes.is_integer_dtype(df[column]),
                f"Expected {column} to be an integer dtype",
            )

        for column in float_columns:
            self.assertTrue(
                ptypes.is_float_dtype(df[column]),
                f"Expected {column} to be a float dtype",
            )

        for column in datetime_columns:
            self.assertTrue(
                ptypes.is_datetime64_dtype(df[column]),
                f"Expected {column} to be a datetime dtype",
            )

        for column in string_columns:
            self.assertTrue(
                ptypes.is_string_dtype(df[column]),
                f"Expected {column} to be a string dtype",
            )

        # Quality_decimal
        self.assertTrue(df["quality_decimal"].max() <= 1.0)
        self.assertTrue(df["quality_decimal"].min() >= 0.0)

        # Signal dBm
        self.assertTrue(df["signal_dBm"].max() <= -30)
        self.assertTrue(df["signal_dBm"].min() >= -120)

        # Dataframe with a location
        location_df = scan(location="Test")

        location_expected_columns = sorted(base_scan_columns + ["location"])
        location_actual_columns = sorted(location_df.columns)

        logger.debug(
            f"Expected columns: {location_expected_columns}, Actual columns: {location_actual_columns}"
        )

        self.assertEqual(location_expected_columns, location_actual_columns)
