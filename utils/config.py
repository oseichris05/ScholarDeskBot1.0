# # utils/config.py

# import os
# from pathlib import Path
# from dotenv import load_dotenv

# # Ensure .env is loaded so environment variables are available
# load_dotenv()

# # Load config.yaml as plain text
# config_path = Path(__file__).parent.parent / "config.yaml"
# if not config_path.exists():
#     raise FileNotFoundError(f"config.yaml not found at {config_path}")

# # Parse YAML
# try:
#     import yaml
# except ImportError:
#     raise ImportError(
#         "PyYAML is required to parse config.yaml. "
#         "Install it with: pip install pyyaml"
#     )

# CONFIG = yaml.safe_load(config_path.read_text())


# utils/config.py

import json
from pathlib import Path
from dotenv import load_dotenv

# 1) Load environment variables from .env
load_dotenv()

# 2) Load JSON config
CONFIG_PATH = Path(__file__).parent.parent / "config.json"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config.json at {CONFIG_PATH}")

with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)
