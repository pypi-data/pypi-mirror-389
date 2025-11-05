import os
import subprocess
from datetime import datetime

import pandas as pd
from template_log_parser import parse_function, compile_templates
from template_log_parser.templates.definitions import SimpleTemplate

base_scan_columns = [
    "time",
    "mac",
    "essid",
    "channel",
    "frequency_GHz",
    "signal_dBm",
    "quality",
    "quality_decimal",
]


def get_wireless_interfaces(net_path: str = "/sys/class/net") -> list[str] | None:
    """
    Returns a list of wireless interface names by checking /sys/class/net, or other designated path

    :param net_path: directory for installed network interface
    :type net_path: str

    :return: list of valid wireless interfaces or None if not found
    :rtype: list[str], None
    """

    if not os.path.isdir(net_path):
        print("Invalid interface path")
        return None

    wireless_interfaces: list[str] = []

    for iface in os.listdir(net_path):
        if os.path.isdir(os.path.join(net_path, iface, "wireless")):
            wireless_interfaces.append(iface)

    if len(wireless_interfaces) == 0:
        print("Unable to locate valid wireless interface")
        return None

    else:
        return wireless_interfaces


def iwlist_command(interface: str = "get") -> str:
    """
    Return raw string text output of command 'iwlist <interface> scan'

    :param interface: name of wireless interface or 'get' to run get_wireless_interfaces()
    :type interface: str

    :return: raw string output of subprocess command
    :rtype: str
    """
    if interface == "get":
        interface_list: list[str] | None = get_wireless_interfaces()
        if interface is None:
            return "No valid interface"
        else:
            interface: str = interface_list[0]

    command: list[str] = ["iwlist", interface, "scan"]

    raw_output: subprocess.CompletedProcess = subprocess.run(
        args=command, stdout=subprocess.PIPE, text=True, stderr=subprocess.PIPE
    )

    output_data: str = str(raw_output)

    fail_conditions: list[str] = [
        "Network is down",
        "Interface doesn't support scanning",
        "Failed",
    ]

    for condition in fail_conditions:
        if condition in output_data:
            output_data: str = f"ERROR: {output_data}"
            return output_data

    return output_data


def get_cells(iwlist_string: str) -> list[str]:
    """
    Return a list of strings from joined lines for each cell in string output of 'iwlist (interface) scan'

    :param iwlist_string: string output of 'iwlist <interface> scan' command
    :type iwlist_string: str

    :return: list of raw strings, one for each cell discovered during scan: empty list if nothing found
    :rtype: list[str]
    """

    cell_lines: list[str] = []

    cells: list[str] = iwlist_string.split("Cell")

    for cell in cells[1:]:
        # pieces: list[str] = cell.splitlines()
        pieces: list[str] = cell.split("\\n")
        cleaned: str = "+".join([item.strip() for item in pieces])
        cell_lines.append(cleaned)

    return cell_lines


def parse_cells(cells: list[str]) -> list[dict[str, str]]:
    """
    Parse string outputs of cells and return a list of dictionaries for appropriate keys/values

    :param cells: list of raw strings, one for each cell discovered during scan or None
    :type cells: list[str]

    :return: list of dictionaries with parsed values for appropriate fields
    :rtype: list[dict[str, str]]
    """

    output: list[dict[str, str]] = []

    cell_template: str = (
        "{cell} - Address: {mac}+"
        "Channel:{channel}+"
        "Frequency:{frequency_GHz} {frequency_info}+"
        "Quality={quality}  Signal level={signal_dBm} dBm+"
        "Encryption key:{encryption_key}+"
        "ESSID:{essid}+"
        "{remaining_info}"
    )

    cell_templates: list[list[str]] = [[cell_template, "cell", " "]]
    templates: list[SimpleTemplate] = compile_templates(cell_templates)

    for line in cells:
        parsed_values: dict[str, str] = parse_function(line, templates)
        output.append(parsed_values)

    return output


def generate_df_from_cells(
    cells: list[dict[str, str]], location: str | None = None
) -> pd.DataFrame:
    """
    Return pandas DataFrame from parsed cells with appropriate dtypes for desired columns, add time and quality_decimal columns

    :param cells: parsed values from 'iwlist <interface> scan'
    :type cells: list[dict[str, str]]

    :param location: (optional) User defined location, will create additional column
    :type location: str

    :return: Dataframe with columns ["time", "mac", "essid", "channel", "frequency_GHz", "signal_dBm", "quality", "quality_decimal"] with optional "location"
    :rtype: pd.DataFrame
    """

    df: pd.DataFrame = pd.DataFrame(cells)

    integer_columns: list[str] = ["channel", "signal_dBm"]
    df[integer_columns] = df[integer_columns].astype(int)

    float_columns: list[str] = ["frequency_GHz"]
    df[float_columns] = df[float_columns].astype(float)

    # Generates a value between 0 and 1 by converting the fraction to a float
    df["quality_decimal"] = df["quality"].apply(
        lambda x: int(x.split("/")[0]) / int(x.split("/")[1])
    )

    # Add time
    df["time"] = datetime.now()

    df: pd.DataFrame = df[base_scan_columns]

    # Add location
    if location:
        df["location"] = location

    return df


def scan(interface: str = "get", location: str | None = None) -> pd.DataFrame:
    """
    Generate a pandas DataFrame by parsing lines from iwlist <interface> scan

    :param interface: name of wireless interface or 'get' to run get_wireless_interfaces()
    :type interface: str

    :param location: (optional) User defined location, will create additional column
    :type location: str

    :return: Dataframe with columns ["time", "mac", "essid", "channel", "frequency_GHz", "signal_dBm", "quality", "quality_decimal"] with optional "location"
    :rtype: pd.DataFrame
    """

    text: str = iwlist_command(interface=interface)

    raw_cells: list[str] = get_cells(iwlist_string=text)

    parsed_cells: list[dict[str, str]] = parse_cells(cells=raw_cells)
    if not parsed_cells:
        print(
            "Unable to parse cells (returning empty DataFrame), please read the following output for clues:"
        )
        print(f"Text from iwlist command: {text}")
        print(f"Cells: {raw_cells}")
        print(f"Parsed cells: {parsed_cells}")

        return pd.DataFrame(parsed_cells)

    df: pd.DataFrame = generate_df_from_cells(cells=parsed_cells, location=location)

    return df
