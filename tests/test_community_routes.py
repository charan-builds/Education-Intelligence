import asyncio
from types import SimpleNamespace

from fastapi import Response

from app.presentation import community_routes
from app.schemas.common_schema import PaginationParams
from app.schemas.community_schema import (
    BadgeCreateRequest,
    CommunityCreateRequest,
    CommunityMemberCreateRequest,
    DiscussionReplyCreateRequest,
    DiscussionThreadCreateRequest,
    DiscussionThreadResolveRequest,
)


class _DummySession:
    pass


class _FakeCommunityService:
    last_create_community = None
    last_join = None
    last_create_thread = None
    last_resolve_thread = None
    last_create_reply = None
    last_award_badge = None
    last_delete_community = None
    last_revoke_badge = None

    def __init__(self, session):
        self.session = session

    async def list_communities_page(self, **kwargs):
        return {
            "items": [
                {
                    "id": 1,
                    "tenant_id": kwargs["tenant_id"],
                    "topic_id": 7,
                    "name": "ML Community",
                    "description": "Machine learning peers",
                    "created_at": "2026-03-14T00:00:00Z",
                    "topic_name": "Machine Learning",
                    "member_count": 2,
                    "thread_count": 1,
                    "is_member": True,
                }
            ],
            "meta": {"total": 1, "limit": kwargs["limit"], "offset": kwargs["offset"], "next_offset": None, "next_cursor": None},
        }

    async def create_community(self, **kwargs):
        _FakeCommunityService.last_create_community = kwargs
        return SimpleNamespace(
            id=2,
            tenant_id=kwargs["tenant_id"],
            topic_id=kwargs["topic_id"],
            name=kwargs["name"],
            description=kwargs["description"],
            created_at="2026-03-14T00:00:00Z",
            topic_name="Pandas",
            member_count=0,
            thread_count=0,
            is_member=False,
        )

    async def delete_community(self, **kwargs):
        _FakeCommunityService.last_delete_community = kwargs

    async def list_members_page(self, **kwargs):
        return {
            "items": [
                {
                    "id": 1,
                    "tenant_id": kwargs["tenant_id"],
                    "community_id": kwargs["community_id"] or 1,
                    "user_id": 9,
                    "role": "student",
                    "joined_at": "2026-03-14T00:00:00Z",
                    "user_email": "learner@example.com",
                }
            ],
            "meta": {"total": 1, "limit": kwargs["limit"], "offset": kwargs["offset"], "next_offset": None, "next_cursor": None},
        }

    async def join_community(self, **kwargs):
        _FakeCommunityService.last_join = kwargs
        return SimpleNamespace(
            id=3,
            tenant_id=kwargs["tenant_id"],
            community_id=kwargs["community_id"],
            user_id=kwargs["user_id"],
            role=kwargs["role"],
            joined_at="2026-03-14T00:00:00Z",
            user_email="learner@example.com",
        )

    async def list_threads_page(self, **kwargs):
        return {
            "items": [
                {
                    "id": 10,
                    "tenant_id": kwargs["tenant_id"],
                    "community_id": kwargs["community_id"] or 1,
                    "author_user_id": 9,
                    "title": "How should I start?",
                    "body": "Need a study plan",
                    "is_resolved": False,
                    "created_at": "2026-03-14T00:00:00Z",
                    "author_email": "learner@example.com",
                    "community_name": "ML Community",
                }
            ],
            "meta": {"total": 1, "limit": kwargs["limit"], "offset": kwargs["offset"], "next_offset": None, "next_cursor": None},
        }

    async def create_thread(self, **kwargs):
        _FakeCommunityService.last_create_thread = kwargs
        return SimpleNamespace(
            id=11,
            tenant_id=kwargs["tenant_id"],
            community_id=kwargs["community_id"],
            author_user_id=kwargs["author_user_id"],
            title=kwargs["title"],
            body=kwargs["body"],
            is_resolved=False,
            created_at="2026-03-14T00:00:00Z",
            author_email="teacher@example.com",
            community_name="ML Community",
        )

    async def resolve_thread(self, **kwargs):
        _FakeCommunityService.last_resolve_thread = kwargs
        return SimpleNamespace(
            id=kwargs["thread_id"],
            tenant_id=kwargs["tenant_id"],
            community_id=1,
            author_user_id=9,
            title="Need help",
            body="How do I revise?",
            is_resolved=kwargs["is_resolved"],
            created_at="2026-03-14T00:00:00Z",
            author_email="teacher@example.com",
            community_name="ML Community",
        )

    async def list_replies_page(self, **kwargs):
        return {
            "items": [
                {
                    "id": 21,
                    "tenant_id": kwargs["tenant_id"],
                    "thread_id": kwargs["thread_id"],
                    "author_user_id": 9,
                    "body": "Start with the foundations and practice daily.",
                    "created_at": "2026-03-14T00:00:00Z",
                    "author_email": "mentor@example.com",
                }
            ],
            "meta": {"total": 1, "limit": kwargs["limit"], "offset": kwargs["offset"], "next_offset": None, "next_cursor": None},
        }

    async def create_reply(self, **kwargs):
        _FakeCommunityService.last_create_reply = kwargs
        return SimpleNamespace(
            id=22,
            tenant_id=kwargs["tenant_id"],
            thread_id=kwargs["thread_id"],
            author_user_id=kwargs["author_user_id"],
            body=kwargs["body"],
            created_at="2026-03-14T00:00:00Z",
            author_email="learner@example.com",
        )

    async def list_badges_page(self, **kwargs):
        return {
            "items": [
                {
                    "id": 1,
                    "tenant_id": kwargs["tenant_id"],
                    "user_id": 12,
                    "name": "Top Mentor",
                    "description": "Great community help",
                    "awarded_for": "mentorship",
                    "awarded_at": "2026-03-14T00:00:00Z",
                    "user_email": "mentor@example.com",
                }
            ],
            "meta": {"total": 1, "limit": kwargs["limit"], "offset": kwargs["offset"], "next_offset": None, "next_cursor": None},
        }

    async def award_badge(self, **kwargs):
        _FakeCommunityService.last_award_badge = kwargs
        return SimpleNamespace(
            id=2,
            tenant_id=kwargs["tenant_id"],
            user_id=kwargs["user_id"],
            name=kwargs["name"],
            description=kwargs["description"],
            awarded_for=kwargs["awarded_for"],
            awarded_at="2026-03-14T00:00:00Z",
            user_email="mentor@example.com",
        )

    async def revoke_badge(self, **kwargs):
        _FakeCommunityService.last_revoke_badge = kwargs


def _user(role: str):
    return SimpleNamespace(id=9, tenant_id=4, role=SimpleNamespace(value=role))


def test_community_routes(monkeypatch):
    monkeypatch.setattr(community_routes, "CommunityService", _FakeCommunityService)

    async def _run():
        communities = await community_routes.list_communities(
            topic_id=None,
            db=_DummySession(),
            current_user=_user("student"),
            pagination=PaginationParams(limit=20, offset=0, cursor=None),
        )
        assert communities["items"][0]["name"] == "ML Community"

        created = await community_routes.create_community(
            payload=CommunityCreateRequest(topic_id=3, name="Pandas Lab", description="Data work"),
            db=_DummySession(),
            current_user=_user("admin"),
        )
        assert created.name == "Pandas Lab"
        assert _FakeCommunityService.last_create_community["tenant_id"] == 4

        deleted_community = await community_routes.delete_community(
            community_id=2,
            db=_DummySession(),
            current_user=_user("admin"),
        )
        assert isinstance(deleted_community, Response)
        assert _FakeCommunityService.last_delete_community["community_id"] == 2

        joined = await community_routes.join_community(
            payload=CommunityMemberCreateRequest(community_id=1),
            db=_DummySession(),
            current_user=_user("student"),
        )
        assert joined.community_id == 1

        threads = await community_routes.list_threads(
            community_id=1,
            db=_DummySession(),
            current_user=_user("student"),
            pagination=PaginationParams(limit=20, offset=0, cursor=None),
        )
        assert threads["items"][0]["title"] == "How should I start?"

        created_thread = await community_routes.create_thread(
            payload=DiscussionThreadCreateRequest(community_id=1, title="Need help", body="How do I revise?"),
            db=_DummySession(),
            current_user=_user("teacher"),
        )
        assert created_thread.title == "Need help"

        resolved = await community_routes.resolve_thread(
            thread_id=11,
            payload=DiscussionThreadResolveRequest(is_resolved=True),
            db=_DummySession(),
            current_user=_user("teacher"),
        )
        assert resolved.is_resolved is True

        replies = await community_routes.list_replies(
            thread_id=11,
            db=_DummySession(),
            current_user=_user("student"),
            pagination=PaginationParams(limit=20, offset=0, cursor=None),
        )
        assert replies["items"][0]["thread_id"] == 11

        created_reply = await community_routes.create_reply(
            payload=DiscussionReplyCreateRequest(thread_id=11, body="Try a step-by-step plan."),
            db=_DummySession(),
            current_user=_user("student"),
        )
        assert created_reply.thread_id == 11
        assert _FakeCommunityService.last_create_reply["author_user_id"] == 9

        badges = await community_routes.list_badges(
            user_id=None,
            db=_DummySession(),
            current_user=_user("student"),
            pagination=PaginationParams(limit=20, offset=0, cursor=None),
        )
        assert badges["items"][0]["name"] == "Top Mentor"

        awarded = await community_routes.award_badge(
            payload=BadgeCreateRequest(
                user_id=12,
                name="Community Guide",
                description="Helped resolve learning blockers",
                awarded_for="mentorship",
            ),
            db=_DummySession(),
            current_user=_user("admin"),
        )
        assert awarded.name == "Community Guide"

        revoked = await community_routes.revoke_badge(
            badge_id=2,
            db=_DummySession(),
            current_user=_user("admin"),
        )
        assert isinstance(revoked, Response)
        assert _FakeCommunityService.last_revoke_badge["badge_id"] == 2

    asyncio.run(_run())
