import json
from sqlalchemy.types import TypeDecorator, TEXT
from datetime import datetime, timezone

class JSONEncodedDict(TypeDecorator):
    """Custom SQLAlchemy TypeDecorator for JSON that serializes datetime."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value, default=self._datetime_serializer)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value, object_hook=self._datetime_deserializer)

    def _datetime_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not serializable")

    def _datetime_deserializer(self, obj):
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
