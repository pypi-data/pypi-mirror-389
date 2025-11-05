from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml
from google.auth.credentials import Credentials
from google.oauth2 import service_account

def get_credentials(scopes: Optional[list[str]] = None) -> Credentials:
    """
    Returns credentials from config.yml.
    """
    scopes = scopes or ["https://www.googleapis.com/auth/devstorage.read_write"]

    # Load from config.yml
    config_path = Path(__file__).parent.parent.parent / "config.yml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config and 'GOOGLE_APPLICATION_CREDENTIALS' in config:
                gac = config['GOOGLE_APPLICATION_CREDENTIALS']
                if gac:
                    # Resolve credentials path relative to config.yml location
                    creds_path = config_path.parent / gac
                    return service_account.Credentials.from_service_account_file(
                        str(creds_path), scopes=scopes
                    )

    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in config.yml")

