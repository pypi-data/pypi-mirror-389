import unittest


from test.resources import logger

from raspberry_wifi_scanner.calculations import convert_dbm_to_mw, convert_mw_to_dbm, power_leakage

from raspberry_wifi_scanner.definitions import two_gigahertz_channels

dbm_mw_map = {
    -30: 0.001,
    -40: 0.0001,
    -50: 0.00001,
    -60: 0.000001,
    -70: 0.0000001,
    -80: 0.00000001,
    -90: 0.000000001,
    -100: 0.0000000001,
    -110: 0.00000000001,
    -120: 0.000000000001,
}


class TestCalculations(unittest.TestCase):
    """Defines a class to test functions from the calculations module"""

    def test_convert_dbm_to_mw(self):
        """Assert that convert_dbm_to_mw() returns correct float values"""
        for dbm, mw in dbm_mw_map.items():
            converted_value = convert_dbm_to_mw(dbm)
            logger.debug(f"{dbm} dBm converts into {converted_value} mW")
            self.assertEqual(converted_value, mw)

    def test_convert_mw_to_dbm(self):
        """Assert that convert_mw_to_dbm() return the correct integer values"""
        for dbm, mw in dbm_mw_map.items():
            converted_value = convert_mw_to_dbm(mw)
            logger.debug(f"{mw} mW converts into {converted_value} dBm")
            self.assertEqual(dbm, converted_value)

    def test_power_leakage(self):
        """Assert that power_leakage() returns appropriate approximated values"""
        floor = -120
        floor_mw = convert_dbm_to_mw(floor)
        drop_per_channel = 10
        for channel in two_gigahertz_channels:
            center = channel
            logger.debug(f"Checking center channel: {center}")
            for dbm in dbm_mw_map.keys():
                logger.debug(f"Checking {dbm} dbm")
                for spread in range(1, 11):
                    logger.debug(f"Checking spread {spread}")
                    output = power_leakage(
                        dbm=dbm,
                        center_channel=center,
                        valid_channels=two_gigahertz_channels,
                        drop_db_per_channel=drop_per_channel,
                        floor_dbm=floor,
                        spread=spread,
                    )

                    # Account for all valid channels
                    self.assertEqual(len(output), len(two_gigahertz_channels))

                    # All values outside the spread should equal the floor dbm converted mw power value
                    values_outside_spread = [
                        value
                        for value in two_gigahertz_channels
                        if abs(center - value) > spread
                    ]
                    logger.debug(
                        f"Checking values outside the spread: {values_outside_spread}"
                    )
                    for value in values_outside_spread:
                        leaked_power = output.get(value)
                        self.assertEqual(leaked_power, floor_mw)

                    # Values inside the spread should have dbm drop x distance away from center, converted to a power value
                    values_inside_spread = [
                        value
                        for value in two_gigahertz_channels
                        if abs(center - value) <= spread
                    ]
                    logger.debug(
                        f"Checking values inside the spread: {values_inside_spread}"
                    )
                    for value in values_inside_spread:
                        leaked_power = output.get(value)
                        logger.debug(f"Actual leaked power: {leaked_power}")
                        expected_leaked_dbm = dbm - (
                            abs(center - value) * drop_per_channel
                        )
                        # Nothing should be lower than the floor
                        expected_leaked_dbm = max(expected_leaked_dbm, floor)
                        logger.debug(f"Expected leaked dBm: {expected_leaked_dbm}")
                        expected_leaked_power = convert_dbm_to_mw(expected_leaked_dbm)
                        logger.debug(f"Expected leaked power: {expected_leaked_power}")
                        self.assertEqual(leaked_power, expected_leaked_power)
