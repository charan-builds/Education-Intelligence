from pydantic import BaseModel, Field


class NotificationItemResponse(BaseModel):
    id: int
    notification_type: str
    severity: str
    title: str
    message: str
    action_url: str | None = None
    created_at: str
    read_at: str | None = None


class NotificationListResponse(BaseModel):
    notifications: list[NotificationItemResponse] = Field(default_factory=list)


class NotificationReadResponse(NotificationItemResponse):
    pass
