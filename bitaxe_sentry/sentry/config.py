from dotenv import load_dotenv
import os
import pathlib
import logging

logger = logging.getLogger(__name__)

# Find .env file (look in parent directory if not in current)
env_path = pathlib.Path(__file__).parent.parent / '.env'
if not env_path.exists():
    # Try looking in the project root (when running with Docker or from repo root)
    env_path = pathlib.Path(__file__).parent.parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

# Configuration parameters
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_MINUTES", 15))
logger.info(f"Configured polling interval: {POLL_INTERVAL} minutes")

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))
TEMP_MIN = float(os.getenv("TEMP_MIN", 20))
TEMP_MAX = float(os.getenv("TEMP_MAX", 70))
VOLT_MIN = float(os.getenv("VOLT_MIN", 5.0))

# Process endpoints
endpoints = os.getenv("BITAXE_ENDPOINTS", "").split(",")
ENDPOINTS = []
for ep in endpoints:
    ep = ep.strip()
    if ep:
        # Ensure each endpoint has a protocol
        if not ep.startswith(("http://", "https://")):
            ep = f"http://{ep}"
        ENDPOINTS.append(ep)

logger.info(f"Configured endpoints: {ENDPOINTS}")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL") 