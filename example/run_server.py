#!/usr/bin/env python3
"""Start Soliplex server in no-auth mode."""

from pathlib import Path

import uvicorn
from soliplex.main import create_app

app = create_app(
    installation_path=Path("installation.yaml"),
    no_auth_mode=True,
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
