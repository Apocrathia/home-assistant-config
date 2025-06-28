#!/usr/bin/env python3

import argparse
import json
import shutil

def remove_devices_with_matching_field(file_path, field, value):
    """
    Remove devices with a specified field containing a specified value.

    Parameters:
    - file_path (str): The path to the JSON file containing device data.
    - field (str): The device field to be evaluated.
    - value (str): The value to match within the specified field.

    The function creates a backup of the original JSON file by appending a '.bak'
    to the original file name. Devices in the original file with the specified field
    containing the specified value are removed.

    Returns:
    None
    """

    # Create a backup of the original file
    backup_file_path = file_path + ".bak"
    shutil.copyfile(file_path, backup_file_path)

    count = 0

    with open(file_path, 'r') as file:
        data = json.load(file)

    devices = data["data"]["devices"]
    filtered_devices = []

    for device in devices:
        field_value = device.get(field)
        if field_value:
            # Handle both string and list field values
            if isinstance(field_value, list):
                # If it's a list, check if any item contains the value
                if any(value in str(item) for item in field_value):
                    count += 1
                else:
                    filtered_devices.append(device)
            else:
                # If it's a string (or other type), check if the value is in it
                if value in str(field_value):
                    count += 1
                else:
                    filtered_devices.append(device)
        else:
            filtered_devices.append(device)

    data["data"]["devices"] = filtered_devices

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

    print(f"{count} devices with matching field removed. Backup created at: {backup_file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    Remove devices with matching field value from a JSON file.

    This script allows you to filter out devices from a JSON file by specifying
    a field and its value. If the field of any device contains the specified value,
    that device will be removed. The script will create a backup of the original
    file before making any changes.
    """)
    parser.add_argument("file", help="Path to the device JSON file")
    parser.add_argument("field", help="Device field to evaluate")
    parser.add_argument("value", help="Value to match within the specified device field")

    args = parser.parse_args()

    remove_devices_with_matching_field(args.file, args.field, args.value)
