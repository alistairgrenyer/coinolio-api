from datetime import datetime
import json
from typing import Any

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """Helper function to dump JSON with custom encoder"""
    return json.dumps(obj, cls=CustomJSONEncoder)
