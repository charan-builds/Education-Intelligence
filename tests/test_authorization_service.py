import asyncio

from app.core.auth_context import AuthContext
from app.core.authorization import AuthorizationService
from app.domain.models.user import User, UserRole


class _Session:
    async def execute(self, _stmt):
        class _Result:
            def scalars(self):
                class _Scalars:
                    def all(self):
                        return []

                return _Scalars()

        return _Result()


def test_admin_permission_allowed_from_role_map():
    async def _run():
        user = User(
            id=1,
            tenant_id=10,
            email="admin@example.com",
            display_name=None,
            password_hash="x",
            role=UserRole.admin,
            experience_points=0,
            current_streak_days=0,
            focus_score=0.0,
            created_at=None,  # type: ignore[arg-type]
        )
        auth = AuthContext(user=user, actor_user_id=1, actor_tenant_id=10, effective_tenant_id=10)
        allowed = await AuthorizationService(_Session()).is_allowed(user=auth, permission="feature_flags:update")
        assert allowed is True

    asyncio.run(_run())
