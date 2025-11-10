from __future__ import annotations

import anyio
import pytest


async def _runner(coro):
    return await coro


def run_async(awaitable):
    return anyio.run(_runner, awaitable)


@pytest.fixture(scope="session")
def run():
    return run_async
