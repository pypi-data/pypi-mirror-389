# Pi Flows - Search Pipeline Flows

This directory contains the built-in search flows for the search service.

## Structure

```
builtin_flows/
└── pi_flows/              # Standard Python module containing flows
    ├── __init__.py        # Auto-imports all flow files
    ├── search_demo.py
    ├── search_nlweb.py
    ├── search_nlweb_newapi.py
    └── search_simple.py
```

## Using Built-in Flows (Default)

By default, the search service uses these built-in flows:

```bash
python -m search_service
```

The service automatically adds `builtin_flows/` to `sys.path` and imports `pi_flows`.

## Creating Custom Flows

To use custom flows instead of the built-in ones:

### 1. Create your flows directory structure

```bash
mkdir -p /opt/my-flows/pi_flows
```

### 2. Copy the template `__init__.py`

You can use the auto-discovery template from this directory:

```python
# /opt/my-flows/pi_flows/__init__.py
from pathlib import Path
import importlib

# Auto-discover and import all .py files in this directory
flows_dir = Path(__file__).parent

for module_path in flows_dir.glob("*.py"):
    if module_path.name != "__init__.py" and not module_path.name.startswith("_"):
        module_name = module_path.stem
        importlib.import_module(f".{module_name}", package=__package__)
```

Or structure it manually however you prefer:

```python
# /opt/my-flows/pi_flows/__init__.py
from . import search_production
from . import search_staging
```

### 3. Add your flow files

```python
# /opt/my-flows/pi_flows/search_production.py
from pilabs.data_model import Params, SearchQuery, SearchResults
from pilabs.data_model.piragbox_model import piragbox

@piragbox(params={"my_param": "value"})
async def search_production(query: SearchQuery, ranking_params: Params) -> SearchResults:
    # Your custom search logic
    return SearchResults(results_data=[])
```

### 4. Set PYTHONPATH and run

```bash
export PYTHONPATH=/opt/my-flows:$PYTHONPATH
python -m search_service
```

## How It Works

The `main.py` module uses this import logic:

```python
try:
    import pi_flows  # Try importing from PYTHONPATH first
    print("Loaded pi_flows from PYTHONPATH")
except ImportError:
    # Fall back to builtin flows
    sys.path.insert(0, str(Path(__file__).parent / "builtin_flows"))
    import pi_flows
```

This allows:

- **Standard Python packaging**: `pi_flows` is a regular Python module
- **PYTHONPATH-based configuration**: Standard Python mechanism, no custom variables
- **Flexibility**: Users can structure their `pi_flows` module however they want
- **Validation**: `main.py` verifies at least one `@piragbox` pipeline is registered

## Packaging Custom Flows

Your custom `pi_flows` can be packaged as a standard Python package:

```
my-flows-package/
├── setup.py
├── pyproject.toml
└── pi_flows/
    ├── __init__.py
    └── search_*.py
```

Then install it:

```bash
pip install /path/to/my-flows-package
```

No need to set PYTHONPATH - the package will be available in your Python environment!
