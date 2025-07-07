import json
import os
from typing import Any, Dict, List, Union


def deep_merge(
    source: Union[Dict, List], destination: Union[Dict, List]
) -> Union[Dict, List]:
    """
    Recursively merges source into destination.
    If both are dictionaries, performs a deep merge (source overwrites destination for common keys).
    If both are lists, extends destination with unique elements from source.
    Otherwise, source overwrites destination.
    """
    if isinstance(source, dict) and isinstance(destination, dict):
        for key, value in source.items():
            if (
                key in destination
                and isinstance(destination[key], (dict, list))
                and isinstance(value, (dict, list))
            ):
                destination[key] = deep_merge(value, destination[key])
            else:
                destination[key] = value
        return destination
    elif isinstance(source, list) and isinstance(destination, list):
        if all(isinstance(item, dict) and "id" in item for item in source) and all(
            isinstance(item, dict) and "id" in item for item in destination
        ):

            destination_map = {item["id"]: item for item in destination}
            for item in source:
                if item["id"] in destination_map:
                    destination_map[item["id"]] = deep_merge(
                        item, destination_map[item["id"]]
                    )
                else:
                    destination_map[item["id"]] = item
            return list(destination_map.values())
        else:
            for item in source:
                if item not in destination:
                    destination.append(item)
            return destination
    else:
        return source


def save_api_file(file_path: str, data: Any):
    """Save data to a JSON file, merging if file already exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        existing_data = None
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    print(
                        f"Warning: Could not decode existing JSON from {file_path}. Overwriting."
                    )
                    existing_data = None

        if existing_data is not None:
            # Merge new data into existing data
            merged_data = deep_merge(data, existing_data)
        else:
            merged_data = data

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error saving API file {file_path}: {e}")
