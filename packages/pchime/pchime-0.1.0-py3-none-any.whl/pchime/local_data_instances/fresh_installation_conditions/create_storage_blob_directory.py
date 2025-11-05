import os
from pathlib import Path
from typing import Union

def create_storage_blob_folder() -> Union[Path, None]:
    """
    Creates the 'pchime_blob_storage' folder at the root of the drive.
    Returns the Path object if successful, or None if an error occurs.
    """
    folder_name = "pchime_blob_storage"
    
    # 1. Determine the root path and construct the full path
    root = Path("/") if os.name != "nt" else Path("C:/")
    storage_path = root / folder_name
    
    # Check if the folder already exists to satisfy the user's non-execution constraint
    if storage_path.exists():
        return storage_path
        
    # 2. Attempt creation with error handling
    try:
        # We use exist_ok=True just in case another process creates it 
        # between the check and the call, though the check should mostly
        # prevent this call entirely based on the user's requirement.
        storage_path.mkdir(mode=0o755, exist_ok=True)
        return storage_path
    
    except PermissionError:
        # This is the most common operational error when creating folders 
        # at restricted locations like the root of a drive.
        # In a real application, you would log this error.
        print(f"ERROR: Permission denied to create folder at {storage_path}")
        return None
        
    except OSError as e:
        # Catch other OS-related errors (e.g., read-only file system, invalid path)
        print(f"ERROR: An OS error occurred while creating the folder: {e}")
        return None
    
    except Exception as e:
        # Catch any unexpected errors
        print(f"ERROR: An unexpected error occurred: {e}")
        return None