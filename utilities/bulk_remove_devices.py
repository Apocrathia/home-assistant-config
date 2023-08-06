#!/usr/bin/env python3

import argparse
import json
import shutil

def remove_devices_with_matching_field(file_path, field, value):
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
        if field_value and isinstance(field_value, list) and any(value in item for item in field_value):
            count += 1
        else:
            filtered_devices.append(device)

    data["data"]["devices"] = filtered_devices

    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

    print(f"{count} devices with matching field removed. Backup created at: {backup_file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove devices with matching field value")
    parser.add_argument("file", help="Path to the device file")
    parser.add_argument("field", help="Field to evaluate")
    parser.add_argument("value", help="Value to match")

    args = parser.parse_args()

    remove_devices_with_matching_field(args.file, args.field, args.value)
