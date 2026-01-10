import os
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import hashlib
from datetime import datetime
import mimetypes

# plug and play below
class UserFile(BaseModel):
    path: str
    file_name: str
    file_size: int
    last_modified: datetime
    mime_type: str
    # file_type: str
    file_hash: str


"""
this method is solely for getting the properties of the file
params: folder path -> str
"""
# "/Users/kelvinjou/Documents/GitHub/file-finder-prototype/backend/test_files/text/a_really_long_txt.txt"
def getFileProperties(file_path: str) -> UserFile:
    def hash_file(path: str | Path, algorithm="sha256") -> str:
        h = hashlib.new(algorithm)
        path = Path(path)

        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    
    p = Path(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    res = UserFile(
        path=file_path,
        file_name=p.stem,
        file_size=p.stat().st_size,
        last_modified=datetime.fromtimestamp(p.stat().st_mtime),
        mime_type=mime_type or "application/octet-stream", # if can't determine, will default to octet-stream
        file_hash=hash_file(file_path)
    )
    return res

def read_text_file_content(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

"""
gets the folder based on the file path
whitelists only certain file types (text, audio, images w/ their specific extensions)
get file paths from 
"""

# i.e. backend/test_files/audio/test2.wav
def get_valid_file_from_folder(folder_path: str, allowed_mime_types: Optional[set[str]] = None) -> set[str]:
    """
    Get all files from a folder, optionally filtering by MIME type.
    
    Args:
        folder_path: Path to the folder to search
        allowed_mime_types: Set of allowed MIME types (e.g., {'image/png', 'text/plain', 'audio/wav'})
                           If None, all files are included
    Return:
        returns a set of file paths that can be parsed
    """
    folder = Path(folder_path)

    file_paths = []
    for p in folder.rglob("*"):
        if p.is_file():
            if allowed_mime_types is None:
                file_paths.append(str(p))
            else:
                mime_type, _ = mimetypes.guess_type(str(p))
                if mime_type and mime_type in allowed_mime_types:
                    file_paths.append(str(p))

    for path in file_paths: 
        print(path)
    
    return set(file_paths)

 



# TESTS
if __name__ == "__main__":
    print("=== Test 1: Get all files ===")
    all_files = get_valid_file_from_folder("backend/test_files/")
    print(f"Found {len(all_files)} files\n")
    
    print("=== Test 2: Filter by MIME types ===")
    filtered_files = get_valid_file_from_folder(
        "backend/test_files/",
        {
            'image/png', 'image/jpeg',  # images
            'text/plain', 'application/pdf',  # text
            'audio/mpeg', 'audio/wav', 'audio/ogg'  # audio
        }
    )
    print(f"Found {len(filtered_files)} filtered files\n")
    
    print("=== Test 3: Get file properties ===")
    file = getFileProperties('backend/test_files/text/a_really_long_txt.txt')
    print(f"File: {file.file_name}")
    print(f"Size: {file.file_size} bytes")
    print(f"MIME type: {file.mime_type}")
    print(f"Hash: {file.file_hash}")


            
