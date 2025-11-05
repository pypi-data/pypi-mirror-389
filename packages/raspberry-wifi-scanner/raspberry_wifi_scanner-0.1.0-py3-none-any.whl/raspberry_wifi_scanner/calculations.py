import numpy as np


def convert_dbm_to_mw(dbm: int | float) -> float:
    """
    Convert dBm to value representing milliwatts of power

    :param dbm: numerical value dBm, example -50
    :type dbm: int

    :return: milliwatts of power
    :rtype: float
    """

    mw: float = 10 ** (dbm / 10)

    return mw


def convert_mw_to_dbm(mw: float) -> int | float:
    """
    Convert mW of power representing dBm signal strength

    :param mw: numerical value of mW, example 0.0001
    :type mw: int

    :return: dBm signal strength
    :rtype: float
    """

    dbm: int | float = 10 * np.log10(mw)

    return dbm


def power_leakage(
    dbm: int,
    center_channel: int,
    valid_channels: list[int],
    drop_db_per_channel: int = 10,
    floor_dbm: int = -120,
    spread: int = 3,
) -> dict[int, float]:
    """
    Approximate signal leakage onto nearby Wi-Fi channels.
    This is a very rough estimation suited for 20 MHz channel width and will not be helpful for varied widths.

    :param dbm: signal level on center channel
    :type dbm: int

    :param center_channel: channel on which network is located
    :type center_channel: int

    :param valid_channels: list of valid channels for a given area
    :type valid_channels: list[int]

    :param drop_db_per_channel: signal level in dbm of expected drop in channel moving away from center channel
    :type drop_db_per_channel: int

    :param floor_dbm: lowest dbm value, essentially the noise floor
    :type floor_dbm: int

    :param spread: number of channels away from center that experience power leakage, everything beyond to be valued at floor_dbm
    :type spread: int

    :return: key/value of all valid channels and approximate power transmission (mW) on that channel
    :rtype: dict[int, float]
    """

    negligible_mw: float = convert_dbm_to_mw(floor_dbm)

    output: dict[int, float] = {}
    for ch in valid_channels:
        offset: int = abs(ch - center_channel)
        if offset <= spread:
            leak_dbm: int = dbm - (offset * drop_db_per_channel)
            leak_mw: float = max(convert_dbm_to_mw(leak_dbm), negligible_mw)
            output[ch] = leak_mw
        else:
            output[ch] = convert_dbm_to_mw(floor_dbm)
    return output
