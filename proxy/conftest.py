"""Root conftest for proxy tests - ensures the proxy package is importable."""

import sys
from pathlib import Path

# Add the proxy directory to sys.path so both import styles work
proxy_dir = Path(__file__).parent
if str(proxy_dir) not in sys.path:
    sys.path.insert(0, str(proxy_dir))
