"""
Pi Flows - Search Pipeline Flows

This module auto-imports all flow files in this directory, ensuring that
@piragbox decorated functions are registered with the pipeline system.

Users can copy this template for custom flow modules or structure their
pi_flows module however they prefer.
"""

import importlib
from pathlib import Path

# Auto-discover and import all .py files in this directory
flows_dir = Path(__file__).parent

for module_path in flows_dir.glob("*.py"):
    if module_path.name != "__init__.py" and not module_path.name.startswith("_"):
        module_name = module_path.stem
        importlib.import_module(f".{module_name}", package=__package__)
