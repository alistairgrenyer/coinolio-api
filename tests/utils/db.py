import json

from sqlalchemy import JSON, Text, TypeDecorator


class SqliteJson(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

def get_json_type(is_sqlite=False):
    """Returns the appropriate JSON type based on the database."""
    if is_sqlite:
        return SqliteJson
    return JSON
