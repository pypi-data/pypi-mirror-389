import pandas as pd

from raspberry_wifi_scanner.definitions import two_gigahertz_channels
from raspberry_wifi_scanner.calculations import power_leakage, convert_dbm_to_mw, convert_mw_to_dbm


def split_by_band(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return two dataframes: 2.4 GHz networks and 5/6 GHz networks

    :param df: Dataframe containing a "channel" column
    :type df: pd.Dataframe

    :return: 2.4 GHz networks and 5/6 GHz networks
    :rtype: tuple[pd.DataFrame, pd.Dataframe]
    """

    two_four_df: pd.DataFrame = df[df["channel"].isin(two_gigahertz_channels)].copy()
    five_plus_df: pd.DataFrame = df[~df["channel"].isin(two_gigahertz_channels)].copy()

    return two_four_df, five_plus_df


def split_by_mac_list(
    df: pd.DataFrame, macs_to_include: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return to dataframes: one for mac addresses that are included in the list, one for macs that are not.
    This can be useful to isolate your own network(s) from the local area to analyze channel occupancy, dbm, etc.

    :param df: Dataframe containing a "mac" column
    :type df: pd.DataFrame

    :param macs_to_include: list of mac addresses in a format matching the scan data: ie ["00:00:00:00:00:00", ...]
    :type macs_to_include: list[str]

    :return: One DF for rows whose mac address is included in the list, and a second for rows that are not
    :rtype: tuple[pd.DataFrame, pd.Dataframe]
    """

    include_mask: pd.Series = df["mac"].isin(macs_to_include)

    matching_macs: pd.DataFrame = df[include_mask].copy()
    non_matching_macs: pd.DataFrame = df[~include_mask].copy()

    return matching_macs, non_matching_macs


def dbm_per_channel(
    df: pd.DataFrame, valid_channels: list[int], overlap: bool = False
) -> pd.DataFrame:
    """
    Return a DataFrame that provides overall dBm activity for all channels in the given list, overlap optional.

    :param df: Dataframe containing columns ["channel", "signal_dBm"]
    :type df: pd.DataFrame

    :param valid_channels: list of channels to investigate
    :type valid_channels: list[int]

    :param overlap: (Optional) if True, take overlapping channel approximations into account
    :type overlap: bool

    :return: DataFrame with summed values for all provided channels
    :rtype: pd.DataFrame
    """

    df: pd.DataFrame = df.copy()

    if overlap:
        calcs: pd.DataFrame = df.apply(
            lambda row: power_leakage(
                row["signal_dBm"], row["channel"], valid_channels
            ),
            axis=1,
            result_type="expand",
        )
        calcs: pd.DataFrame = calcs[valid_channels].sum().reset_index()
        calcs: pd.DataFrame = calcs.rename(columns={"index": "channel", 0: "power_mW"})

    else:
        df: pd.DataFrame = df[df["channel"].isin(valid_channels)]
        df["power_mW"] = df["signal_dBm"].apply(convert_dbm_to_mw)
        calcs: pd.DataFrame = df.groupby("channel")["power_mW"].sum().reset_index()

    calcs["overall_dBm"]: pd.DataFrame = calcs["power_mW"].apply(convert_mw_to_dbm)

    return calcs
