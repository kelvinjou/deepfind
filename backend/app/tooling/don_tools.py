# Tooling to organize and manage files within the application

import os
import plistlib
import shutil
from pathlib import Path
from typing import List

# Move all files into a specified directory, creating the directory if it doesn't exist
def move_files_to_directory(file_paths: List[str], target_directory: str) -> None:
    os.makedirs(target_directory, exist_ok=True)
    for file_path in file_paths:
        if os.path.isfile(file_path):
            shutil.move(file_path, os.path.join(target_directory, os.path.basename(file_path)))
        else:
            print(f"File not found: {file_path}")
            
# Convert file types from one format to another
def convert_file_types(file_paths: List[str], target_extension: str) -> None:
    for file_path in file_paths:
        base, ext = os.path.splitext(file_path)
        new_file_path = f"{base}.{target_extension.lstrip('.')}"
        try:
            shutil.copy(file_path, new_file_path)
            print(f"Converted {file_path} to {new_file_path}")
        except Exception as e:
            print(f"Error converting {file_path}: {e}")
            
            
def rename_files(file_paths: List[str], new_names: List[str]) -> None:
    if len(file_paths) != len(new_names):
        print("The number of files and new names must be the same.")
        return
    
    for file_path, new_name in zip(file_paths, new_names):
        dir_name = os.path.dirname(file_path)
        new_file_path = os.path.join(dir_name, new_name)
        try:
            os.rename(file_path, new_file_path)
            print(f"Renamed {file_path} to {new_file_path}")
        except Exception as e:
            print(f"Error renaming {file_path}: {e}")


# Delete specified files (DO NOT USE WITHOUT CONFIRMATION)
def delete_files(file_paths: List[str]) -> None:
    for file_path in file_paths:
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

# Tag files (for Mac) - uses native xattr, no third-party tools needed
def tag_files(file_paths: List[str], tag: str, color: int = 0) -> None:
    """
    Tag files with macOS Finder tags.
    
    Args:
        file_paths: List of file paths to tag
        tag: The tag name (e.g., "Work", "Important")
        color: Color index 0-7 (0=none, 1=gray, 2=green, 3=purple, 4=blue, 5=yellow, 6=red, 7=orange)
    """
    import plistlib
    import subprocess
    
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
                
            # Create the tag plist data with color
            tag_with_color = f"{tag}\n{color}" if color > 0 else tag
            tags = [tag_with_color]
            plist_data = plistlib.dumps(tags, fmt=plistlib.FMT_BINARY)
            
            # Set the tag using xattr (hex-encoded binary plist)
            subprocess.run(
                ["xattr", "-wx", "com.apple.metadata:_kMDItemUserTags", plist_data.hex(), file_path],
                check=True,
                capture_output=True
            )
            print(f"Tagged {file_path} with tag: {tag}")
        except subprocess.CalledProcessError as e:
            print(f"Error tagging {file_path}: {e.stderr.decode() if e.stderr else e}")
        except Exception as e:
            print(f"Error tagging {file_path}: {e}")
            
# Get files with a specific tag
def get_files_with_tag(directory: str, tag: str) -> List[str]:
    tagged_files = []
    import subprocess
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                result = subprocess.run(
                    ["xattr", "-px", "com.apple.metadata:_kMDItemUserTags", file_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    tags_data = bytes.fromhex(result.stdout.strip())
                    tags = plistlib.loads(tags_data)
                    if tag in tags:
                        tagged_files.append(file_path)
            except Exception as e:
                print(f"Error retrieving tags for {file_path}: {e}")
    return tagged_files

            
# Search by file name pattern
def search_files_by_pattern(directory: str, pattern: str) -> List[str]:
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if pattern in file:
                matched_files.append(os.path.join(root, file))
    return matched_files

# Search by file tags (metadata)
def search_files_by_tags(directory: str, tag_key: str, tag_value: str) -> List[str]:
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.meta'):
                meta_file_path = os.path.join(root, file)
                try:
                    with open(meta_file_path, 'r') as meta_file:
                        for line in meta_file:
                            key, value = line.strip().split(': ', 1)
                            if key == tag_key and value == tag_value:
                                original_file = meta_file_path[:-5]  # Remove .meta extension
                                matched_files.append(original_file)
                except Exception as e:
                    print(f"Error reading metadata from {meta_file_path}: {e}")
    return matched_files

# Filter files by date range
def filter_files_by_date(directory: str, start_date: float, end_date: float) -> List[str]:
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_mtime = os.path.getmtime(file_path)
                if start_date <= file_mtime <= end_date:
                    matched_files.append(file_path)
            except Exception as e:
                print(f"Error accessing {file_path}: {e}")
    return matched_files

# Filter files by size range
def filter_files_by_size(directory: str, min_size: int, max_size: int) -> List[str]:
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                if min_size <= file_size <= max_size:
                    matched_files.append(file_path)
            except Exception as e:
                print(f"Error accessing {file_path}: {e}")
    return matched_files

# Filter files by type
def filter_files_by_type(directory: str, file_extension: str) -> List[str]:
    matched_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extension):
                matched_files.append(os.path.join(root, file))
    return matched_files

def make_copy_of_files(file_paths: List[str], target_directory: str) -> None:
    os.makedirs(target_directory, exist_ok=True)
    for file_path in file_paths:
        if os.path.isfile(file_path):
            shutil.copy(file_path, os.path.join(target_directory, os.path.basename(file_path)))
        else:
            print(f"File not found: {file_path}")
            
def make_copy_of_directory(source_directory: str, target_directory: str) -> None:
    try:
        shutil.copytree(source_directory, target_directory)
        print(f"Copied directory {source_directory} to {target_directory}")
    except Exception as e:
        print(f"Error copying directory: {e}")
        
# Get most recently modified files
def get_most_recently_modified_files(directory: str, n: int) -> List[str]:
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(file_path)
                all_files.append((file_path, mtime))
            except Exception as e:
                print(f"Error accessing {file_path}: {e}")
    
    all_files.sort(key=lambda x: x[1], reverse=True)
    return [file[0] for file in all_files[:n]]
