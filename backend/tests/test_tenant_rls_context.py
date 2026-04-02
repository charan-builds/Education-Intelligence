import asyncio

from app.infrastructure.tenant_rls import apply_rls_context


class _Session:
    def __init__(self):
        self.calls = []

    async def execute(self, stmt, params=None):
        self.calls.append((str(stmt), params))
        return None


def test_apply_rls_context_sets_session_variables():
    async def _run():
        session = _Session()
        await apply_rls_context(session, tenant_id=7, role="admin", actor_user_id=42)  # type: ignore[arg-type]
        assert len(session.calls) == 3
        assert session.calls[0][1] == {"value": "7"}
        assert session.calls[1][1] == {"value": "admin"}
        assert session.calls[2][1] == {"value": "42"}

    asyncio.run(_run())
