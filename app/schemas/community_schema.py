from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common_schema import PageMeta


class CommunityCreateRequest(BaseModel):
    topic_id: int
    name: str
    description: str


class CommunityResponse(BaseModel):
    id: int
    tenant_id: int
    topic_id: int
    name: str
    description: str
    created_at: datetime
    topic_name: str | None = None
    member_count: int = 0
    thread_count: int = 0
    is_member: bool = False

    model_config = ConfigDict(from_attributes=True)


class CommunityPageResponse(BaseModel):
    items: list[CommunityResponse]
    meta: PageMeta


class CommunityMemberCreateRequest(BaseModel):
    community_id: int


class CommunityMemberResponse(BaseModel):
    id: int
    tenant_id: int
    community_id: int
    user_id: int
    role: str
    joined_at: datetime
    user_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CommunityMemberPageResponse(BaseModel):
    items: list[CommunityMemberResponse]
    meta: PageMeta


class DiscussionThreadCreateRequest(BaseModel):
    community_id: int
    title: str
    body: str


class DiscussionThreadResolveRequest(BaseModel):
    is_resolved: bool = True


class DiscussionThreadResponse(BaseModel):
    id: int
    tenant_id: int
    community_id: int
    author_user_id: int
    title: str
    body: str
    is_resolved: bool
    created_at: datetime
    author_email: str | None = None
    community_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiscussionThreadPageResponse(BaseModel):
    items: list[DiscussionThreadResponse]
    meta: PageMeta


class DiscussionReplyCreateRequest(BaseModel):
    thread_id: int
    body: str


class DiscussionReplyResponse(BaseModel):
    id: int
    tenant_id: int
    thread_id: int
    author_user_id: int
    body: str
    created_at: datetime
    author_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiscussionReplyPageResponse(BaseModel):
    items: list[DiscussionReplyResponse]
    meta: PageMeta


class BadgeResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: int
    name: str
    description: str
    awarded_for: str
    awarded_at: datetime
    user_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BadgePageResponse(BaseModel):
    items: list[BadgeResponse]
    meta: PageMeta


class BadgeCreateRequest(BaseModel):
    user_id: int
    name: str
    description: str
    awarded_for: str = "mentorship"
