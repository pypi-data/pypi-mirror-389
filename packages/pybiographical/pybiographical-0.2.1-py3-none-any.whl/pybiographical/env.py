"""Environment variable management and path utilities.

This module validates required environment variables and provides
standardized path accessors for the media processing pipeline.

Required environment variables (must be set in ~/.zshrc):
- MEDIA_INPUT: Source directory for all input data
- MEDIA_PROCESSED: Output directory for processed files
- METADATA_ROOT: Root directory of the metadata project

All environment variables are validated at import time. If any are missing,
the script will exit with an error message.
"""

import os
import sys


REQUIRED_ENV_VARS = ['MEDIA_INPUT', 'MEDIA_PROCESSED', 'METADATA_ROOT']


def check_environment_variables():
    """Check that all required environment variables are set.
    
    Exits with status 1 if any variables are missing, printing
    helpful error messages to stderr.
    """
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print(f"ERROR: Required environment variables not set: {', '.join(missing)}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please set these variables in your ~/.zshrc file:", file=sys.stderr)
        for var in missing:
            print(f"  export {var}=/path/to/{var.lower()}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Then reload your shell configuration:", file=sys.stderr)
        print("  source ~/.zshrc", file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(1)


# Export environment variables (only if set)
# Note: For public library use, these are optional.
# Call check_environment_variables() explicitly if you need validation.
MEDIA_INPUT = os.environ.get('MEDIA_INPUT', '')
MEDIA_PROCESSED = os.environ.get('MEDIA_PROCESSED', '')
METADATA_ROOT = os.environ.get('METADATA_ROOT', '')


# Common path accessors
def persons_dir():
    """Get the path to the persons directory in metadata project.
    
    Returns:
        str: Path to metadata/data/persons
    """
    return os.path.join(METADATA_ROOT, 'data', 'persons')


def locations_file():
    """Get the path to the locations JSON file in metadata project.
    
    Returns:
        str: Path to metadata/data/locations.json
    """
    return os.path.join(METADATA_ROOT, 'data', 'locations.json')


def locations_dir():
    """Get the path to the locations directory in metadata project.
    
    Returns:
        str: Path to metadata/data/locations
    """
    return os.path.join(METADATA_ROOT, 'data', 'locations')


def extracted_photos_dir():
    """Get the path to the extracted photos directory.
    
    Returns:
        str: Path to MEDIA_PROCESSED/extracted_photos
    """
    return os.path.join(MEDIA_PROCESSED, 'extracted_photos')


def ensure_dir(path):
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to create
        
    Returns:
        str: The path that was ensured (same as input)
    """
    os.makedirs(path, exist_ok=True)
    return path
