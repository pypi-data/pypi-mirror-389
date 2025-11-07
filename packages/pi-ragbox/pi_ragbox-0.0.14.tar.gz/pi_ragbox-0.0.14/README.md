# pi-ragbox

Pi-RagBox CLI tool for managing and interacting with your RAG system on Pi Labs.

## Installation

```bash
pip install pi-ragbox
```

## Usage

### Authentication

Before using the CLI, you need to authenticate with your Pi Labs account:

```bash
# Log in with your Google account
pi-ragbox login

# Check who you're logged in as
pi-ragbox whoami

# Log out
pi-ragbox logout
```

The `login` command will open a browser window for Google OAuth authentication. After successful login, your session cookies are stored locally in `~/.pi-ragbox/config.json` and used for all subsequent API calls.

### Managing Projects

```bash
# List all your projects
pi-ragbox projects
```

### Other Commands

```bash
# Display help
pi-ragbox --help

# Check version
pi-ragbox version
```

## Configuration

The CLI can be configured using an environment variable:

- **`PI_RAGBOX_URL`**: Base URL for the application (default: `https://withpi.ai`)
  - Used for both API calls and browser-based authentication
  - Example: `export PI_RAGBOX_URL=https://withpi.ai`

### Example Configuration

For development (connecting to local instance):
```bash
export PI_RAGBOX_URL=http://localhost:3000
pi-ragbox login
```

For production:
```bash
export PI_RAGBOX_URL=https://withpi.ai
pi-ragbox login
```

Or simply use the default (no configuration needed for production):
```bash
pi-ragbox login  # Uses https://withpi.ai by default
```

## Development

This package is still under development and will change substantially.

### Building

```bash
cd backend/pi-ragbox
python -m build
```

### Publishing

The package is published to PyPI using GitHub Actions. See `.github/workflows/publish-pypi.yml` for details.
