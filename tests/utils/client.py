"""Custom test client implementation."""
import json
from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient
from httpx import AsyncClient


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """Helper function to dump JSON with custom encoder"""
    return json.dumps(obj, cls=CustomJSONEncoder)

class CustomTestClient(TestClient):
    """Custom test client that handles JSON serialization properly"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.async_client = None

    async def __aenter__(self):
        self.async_client = AsyncClient(app=self.app, base_url=self.base_url)
        return self.async_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.async_client:
            await self.async_client.aclose()
            self.async_client = None

    def post(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = json_dumps(kwargs.pop('json')).encode('utf-8')
            kwargs['headers'] = {**kwargs.get('headers', {}), 'Content-Type': 'application/json'}
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = json_dumps(kwargs.pop('json')).encode('utf-8')
            kwargs['headers'] = {**kwargs.get('headers', {}), 'Content-Type': 'application/json'}
        return super().put(*args, **kwargs)
    
    def get(self, *args, **kwargs):
        """Override get to handle JSON response"""
        response = super().get(*args, **kwargs)
        return response
