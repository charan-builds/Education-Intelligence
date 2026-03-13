from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.infrastructure.repositories.topic_repository import TopicRepository


class TopicService:
    def __init__(self, session: AsyncSession):
        self.repository = TopicRepository(session)

    async def get_topic_detail(self, topic_id: int) -> dict:
        topic = await self.repository.get_topic(topic_id)
        if topic is None:
            raise NotFoundError("Topic not found")

        questions = await self.repository.list_questions_for_topic(topic_id)

        # Deterministic examples derived from topic metadata for MVP.
        examples: list[str] = []
        if topic.description:
            parts = [part.strip() for part in topic.description.split(".") if part.strip()]
            examples.extend(parts[:2])
        if not examples:
            examples = [f"Core example for {topic.name}", f"Applied example for {topic.name}"]

        return {
            "id": topic.id,
            "name": topic.name,
            "description": topic.description,
            "examples": examples,
            "practice_questions": [
                {
                    "id": question.id,
                    "difficulty": question.difficulty,
                    "question_text": question.question_text,
                }
                for question in questions
            ],
        }
