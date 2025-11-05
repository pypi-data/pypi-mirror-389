"""Configuration for Laurelin CLI."""
import os
from pathlib import Path

# API Configuration
DEFAULT_API_URL = os.environ.get('LAURELIN_API_URL', 'http://localhost:8080/api')
PRODUCTION_API_URL = 'https://laurelin-chat-backend-975218893454.us-central1.run.app/api'

# Paths
CONFIG_DIR = Path.home() / '.laurelin'
CREDENTIALS_FILE = CONFIG_DIR / 'credentials.json'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Token Configuration
ACCESS_TOKEN_HEADER = 'Authorization'
CLI_TOKEN_HEADER = 'X-CLI-Token'

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
