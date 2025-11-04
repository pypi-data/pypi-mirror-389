import json
import yaml
from pathlib import Path
from typing import Any

def load_config(path: str | Path) -> dict:
    """
    Load YAML or JSON configuration file into a dictionary.
    Validates file existence and format.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in [".yaml", ".yml"]:
            config = yaml.safe_load(f)
        elif path.suffix == ".json":
            config = json.load(f)
        else:
            raise ValueError("Config file must be .yaml/.yml or .json")
    
    if config is None:
        raise ValueError(f"Config file {path} is empty or invalid")
    
    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a dictionary, got {type(config)}")
    
    # Validate config structure
    validate_config(config)
    
    return config


def validate_config(config: dict) -> None:
    """
    Validate configuration dictionary for common errors.
    Raises ValueError if invalid settings detected.
    """
    # Valid plot types
    valid_types = ["auto", "line", "scatter", "hist", "bar", "box", 
                   "surface", "heatmap", "quiver"]
    if "type" in config and config["type"] not in valid_types:
        raise ValueError(
            f"Invalid plot type '{config['type']}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Valid save naming schemes
    valid_save_naming = ["timestamp", "overwrite", "numbered", "uuid"]
    if "save_naming" in config and config["save_naming"] not in valid_save_naming:
        raise ValueError(
            f"Invalid save_naming '{config['save_naming']}'. "
            f"Must be one of: {', '.join(valid_save_naming)}"
        )
    
    # Validate numeric ranges
    for limit_key in ["xlim", "ylim"]:
        if limit_key in config:
            val = config[limit_key]
            if not isinstance(val, (list, tuple)) or len(val) != 2:
                raise ValueError(f"{limit_key} must be a list of 2 numbers, e.g. [0, 10]")
            if not all(isinstance(x, (int, float)) for x in val):
                raise ValueError(f"{limit_key} values must be numeric")
            if val[0] >= val[1]:
                raise ValueError(f"{limit_key} first value must be less than second")
    
    # Validate positive integers
    for int_key in ["bins", "dpi"]:
        if int_key in config:
            val = config[int_key]
            if not isinstance(val, int) or val <= 0:
                raise ValueError(f"{int_key} must be a positive integer")
    
    # Validate size format
    if "size" in config:
        import re
        val = config["size"]
        if not isinstance(val, str) or not re.match(r"^\s*\d+\.?\d*\s*[xX]\s*\d+\.?\d*\s*$", val):
            raise ValueError(f"size must be in format 'WxH' (e.g., '6x4'), got '{val}'")


def merge_config(args, config: dict):
    """
    Merge config dictionary into argparse args.
    CLI arguments take priority over config values.
    Only sets values if they are None, False, or empty string in args.
    """
    for key, value in config.items():
        # Skip keys that don't exist in args
        if not hasattr(args, key):
            continue
        
        current = getattr(args, key)
        
        # Only override if current value is "empty"
        if current in [None, False, ""]:
            setattr(args, key, value)
    
    return args
