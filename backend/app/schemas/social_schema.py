from datetime import datetime

from pydantic import BaseModel, Field


class SocialFollowRequest(BaseModel):
    user_id: int


class SocialProfileResponse(BaseModel):
    user_id: int
    display_name: str
    email: str
    role: str
    xp: int
    streak_days: int
    completion_percent: float
    top_skills: list[str] = Field(default_factory=list)
    weak_topics: list[str] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    communities: list[str] = Field(default_factory=list)
    is_following: bool = False
    follower_count: int = 0
    following_count: int = 0
    tagline: str = ""


class SocialFeedItemResponse(BaseModel):
    actor_user_id: int
    actor_name: str
    event_type: str
    title: str
    description: str
    created_at: datetime
    tone: str = "info"


class SocialPeerGroupResponse(BaseModel):
    title: str
    description: str
    members: list[SocialProfileResponse] = Field(default_factory=list)


class SocialNetworkResponse(BaseModel):
    me: SocialProfileResponse
    following: list[SocialProfileResponse] = Field(default_factory=list)
    suggested_people: list[SocialProfileResponse] = Field(default_factory=list)
    feed: list[SocialFeedItemResponse] = Field(default_factory=list)
    peer_groups: list[SocialPeerGroupResponse] = Field(default_factory=list)
