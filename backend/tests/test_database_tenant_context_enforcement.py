import asyncio

import pytest

from app.infrastructure.database import MissingTenantContextError, TenantAwareAsyncSession


def test_session_execute_requires_explicit_tenant_context():
    async def _run():
        session = TenantAwareAsyncSession()
        with pytest.raises(MissingTenantContextError):
            await TenantAwareAsyncSession.execute(session, "SELECT 1")
        await session.close()

    asyncio.run(_run())
