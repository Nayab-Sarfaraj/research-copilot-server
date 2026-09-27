import importlib
import os
import unittest
from types import SimpleNamespace

from fastapi import HTTPException

os.environ.setdefault("DATABASE_URL", "sqlite://")

rate_limit = importlib.import_module("research_copilot_server.dependencies.rate_limit").rate_limit


class RateLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_limit_is_per_user_and_returns_retry_after(self) -> None:
        enforce_rate_limit = rate_limit("test-resource", 2, 60)
        first_user = SimpleNamespace(id=1)

        await enforce_rate_limit(current_user=first_user)
        await enforce_rate_limit(current_user=first_user)

        with self.assertRaises(HTTPException) as raised:
            await enforce_rate_limit(current_user=first_user)

        self.assertEqual(raised.exception.status_code, 429)
        self.assertIn("Retry-After", raised.exception.headers)
        await enforce_rate_limit(current_user=SimpleNamespace(id=2))


if __name__ == "__main__":
    unittest.main()