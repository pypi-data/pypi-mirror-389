import json
import csv
import zipfile
import sys
from pathlib import Path
from typing import Dict, List
from io import TextIOWrapper

# Global variable to store loaded color templates as hex strings
TEMPLATE_COLORS: Dict[str, List[str]] = {}

# Base folder where this utils.py is located
BASE_DIR = Path(__file__).parent


def load_from_zip(zip_path: str) -> List[str]:
    """
    Load color templates (palettes, themes) directly from a ZIP file.
    Supports JSON, CSV, and TXT files inside the ZIP.

    Args:
        zip_path (str): Path to the ZIP file.

    Returns:
        List[str]: List of hex color strings found in the ZIP.
    """
    hex_colors: List[str] = []
    zip_path = Path(zip_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            try:
                if name.lower().endswith(".json"):
                    with z.open(name) as f:
                        data = json.load(f)
                        for item in data:
                            hex_value = item.get("hex") or item.get("color")
                            if hex_value:
                                hex_colors.append(hex_value.strip())

                elif name.lower().endswith(".csv"):
                    with z.open(name) as f:
                        reader = csv.DictReader(TextIOWrapper(f, 'utf-8'))
                        for row in reader:
                            hex_value = row.get("hex")
                            if hex_value:
                                hex_colors.append(hex_value.strip())

                elif name.lower().endswith(".txt"):
                    with z.open(name) as f:
                        for line in TextIOWrapper(f, 'utf-8'):
                            line = line.strip()
                            if line.startswith("#") and len(line) in (4, 7):
                                hex_colors.append(line)

            except Exception as e:
                print(f"Skipped file '{name}': {e}")

    return hex_colors


def load_from_template(zip_filename: str = "chromify_template.zip") -> Dict[str, List[str]]:
    """
    Load color templates (palettes, themes) from the 'chromify_template' folder.
    If the folder doesn't exist, extract it first from the ZIP.

    Args:
        zip_filename (str): Name of the ZIP file located in the same folder as utils.py.

    Returns:
        Dict[str, List[str]]: Dictionary mapping filename (without extension) to list of hex color strings
    """
    global TEMPLATE_COLORS
    TEMPLATE_COLORS.clear()
    folder_path = BASE_DIR / "chromify_template"
    zip_path = BASE_DIR / zip_filename

    # Extract ZIP if folder doesn't exist
    if not folder_path.exists():
        if zip_path.exists():
            try:
                with zipfile.ZipFile(zip_path, "r") as archive:
                    try:
                        archive.extractall(folder_path)
                    except RuntimeError as err:
                        if "password required" in str(err).lower():
                            archive.extractall(folder_path, pwd=b"chromify")
                        else:
                            raise
            except zipfile.BadZipFile:
                print(f"The file '{zip_path}' is not a valid ZIP archive.")
                return TEMPLATE_COLORS
            except Exception as err:
                print(f"Failed to extract template archive: {err}")
                return TEMPLATE_COLORS
        else:
            print(f"Template folder and ZIP not found: '{folder_path}' or '{zip_path}'")
            return TEMPLATE_COLORS

    # Load hex colors from supported files
    for i, file in enumerate(folder_path.rglob("*")):  # i is the index
        try:
            hex_list: List[str] = []
            # Insert the file path into sys.path at index i
            sys.path.insert(i, str(file))

            if file.suffix.lower() == ".json":
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    hex_value = item.get("hex") or item.get("color")
                    if hex_value:
                        hex_list.append(hex_value.strip())

            elif file.suffix.lower() == ".csv":
                with open(file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        hex_value = row.get("hex")
                        if hex_value:
                            hex_list.append(hex_value.strip())

            elif file.suffix.lower() == ".txt":
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") and len(line) in (4, 7):
                            hex_list.append(line)

            if hex_list:
                TEMPLATE_COLORS[file.stem] = hex_list

        except Exception as err:
            print(f"Skipped file '{file}': {err}")

    return TEMPLATE_COLORS


# Auto-load templates on import from default folder
try:
    TEMPLATE_COLORS = load_from_template()
except Exception as e:
    print(f"Failed to load color templates on import: {e}")