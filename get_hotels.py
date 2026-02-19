# =============================================================================
# Script called by api_hotels.php. Prints the HOTELS list as JSON to stdout
# so the frontend can fetch and display all hotels.
# =============================================================================

import json
import sys
# HOTELS is the in-memory list of hotel dicts (id, name, city, room_types, etc.)
from tools import HOTELS

# Ensure stdout is UTF-8 (for special characters in names/descriptions)
sys.stdout.reconfigure(encoding='utf-8')

# Output JSON array of hotels for PHP to capture and send to the client
print(json.dumps(HOTELS))
