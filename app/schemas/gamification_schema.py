from pydantic import BaseModel, Field


class GamificationEventItemResponse(BaseModel):
    id: int
    event_type: str
    source_type: str
    source_id: int
    topic_id: int | None = None
    diagnostic_test_id: int | None = None
    xp_delta: int
    level_after: int
    streak_after: int
    awarded_at: str


class GamificationProfileResponse(BaseModel):
    tenant_id: int
    user_id: int
    level: int
    total_xp: int
    current_level_xp: int
    xp_to_next_level: int
    current_streak_days: int
    longest_streak_days: int
    completed_topics_count: int
    completed_tests_count: int
    last_activity_on: str | None = None
    recent_events: list[GamificationEventItemResponse] = Field(default_factory=list)


class LeaderboardEntryResponse(BaseModel):
    rank: int
    user_id: int
    display_name: str
    level: int
    total_xp: int
    current_streak_days: int
    completed_topics_count: int
    completed_tests_count: int
    is_current_user: bool


class LeaderboardResponse(BaseModel):
    tenant_id: int
    generated_at: str
    entries: list[LeaderboardEntryResponse] = Field(default_factory=list)
