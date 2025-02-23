import json
from datetime import datetime, timezone
from typing import Any, Optional, Union

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TEXT, TypeDecorator


class JSONEncodedDict(TypeDecorator):
    """Custom SQLAlchemy TypeDecorator for JSON that serializes datetime."""

    impl = TEXT

    def process_bind_param(self, value: Optional[dict[str, Any]], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value, default=self._datetime_serializer)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[dict[str, Any]]:
        if value is None:
            return None
        return json.loads(value, object_hook=self._datetime_deserializer)

    def _datetime_serializer(self, obj: datetime) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not serializable")

    def _datetime_deserializer(self, obj: Union[dict[str, Any], list, str, int, float, bool]) -> Union[dict[str, Any], list, str, int, float, bool]:
        if not isinstance(obj, dict):
            return obj
        for key, val in obj.items():
            if isinstance(val, str):
                try:
                    # Try to parse as ISO format datetime
                    dt = datetime.fromisoformat(val)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    obj[key] = dt
                except ValueError:
                    pass
        return obj
