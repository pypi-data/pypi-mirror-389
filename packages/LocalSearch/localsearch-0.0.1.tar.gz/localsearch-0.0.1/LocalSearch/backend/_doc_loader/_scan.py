# scans the directory


import os, json

METADATA_FILE = ".metadata_cache.json"

def _getDirectoryStatus(path):
    """
    Checks if the directory is new or has changed since last run.
    Returns True if new or any changes detected, False otherwise.
    """
    metadata_path = os.path.join(path, METADATA_FILE)
    changed = False

    # Load existing metadata if it exists
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        metadata = {}
        changed = True  # directory is new

    current_files = {}
    for root, _, files in os.walk(path):
        for f in files:
            if f == METADATA_FILE:  # skip metadata file itself
                continue
            file_path = os.path.join(root, f)
            try:
                stat = os.stat(file_path)
                current_files[file_path] = {
                    "modified": stat.st_mtime,
                    "size": stat.st_size
                }
            except (FileNotFoundError, PermissionError):
                continue

    # Compare with metadata
    for file_path, info in current_files.items():
        if file_path not in metadata:
            changed = True  # new file
            break
        if metadata[file_path]["modified"] != info["modified"] or metadata[file_path]["size"] != info["size"]:
            changed = True  # modified file
            break

    # Update metadata
    with open(metadata_path, "w") as f:
        json.dump(current_files, f, indent=2)

    return changed


