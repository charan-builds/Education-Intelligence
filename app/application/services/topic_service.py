import csv
import io

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.feature_flags import FeatureFlagService
from app.infrastructure.clients.ai_service_client import AIServiceClient
from app.infrastructure.repositories.topic_repository import TopicRepository


class TopicService:
    def __init__(self, session: AsyncSession):
        self.repository = TopicRepository(session)
        self.ai_service_client = AIServiceClient()
        self.feature_flag_service = FeatureFlagService(session)

    async def _repo_get_topic(self, topic_id: int, tenant_id: int):
        try:
            return await self.repository.get_topic(topic_id, tenant_id=tenant_id)
        except TypeError:
            return await self.repository.get_topic(topic_id)

    async def _repo_get_topic_by_name(self, tenant_id: int, name: str):
        try:
            return await self.repository.get_topic_by_name(tenant_id, name)
        except TypeError:
            return await self.repository.get_topic_by_name(name)

    async def _repo_list_questions_for_topic(self, topic_id: int, tenant_id: int):
        try:
            return await self.repository.list_questions_for_topic(topic_id, tenant_id=tenant_id)
        except TypeError:
            return await self.repository.list_questions_for_topic(topic_id)

    async def _repo_list_questions(self, *, limit: int, offset: int, tenant_id: int, topic_id: int | None, question_type: str | None, search: str | None):
        try:
            return await self.repository.list_questions(
                limit=limit,
                offset=offset,
                tenant_id=tenant_id,
                topic_id=topic_id,
                question_type=question_type,
                search=search,
            )
        except TypeError:
            return await self.repository.list_questions(
                limit=limit,
                offset=offset,
                topic_id=topic_id,
                question_type=question_type,
                search=search,
            )

    async def _repo_count_questions(self, *, tenant_id: int, topic_id: int | None, question_type: str | None, search: str | None):
        try:
            return await self.repository.count_questions(
                tenant_id=tenant_id,
                topic_id=topic_id,
                question_type=question_type,
                search=search,
            )
        except TypeError:
            return await self.repository.count_questions(
                topic_id=topic_id,
                question_type=question_type,
                search=search,
            )

    async def list_topics_page(self, limit: int, offset: int, tenant_id: int = 1) -> dict:
        items = await self.repository.get_topics(tenant_id=tenant_id)
        total = len(items)
        page_items = items[offset : offset + limit]
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": page_items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def get_topic_detail(self, topic_id: int, tenant_id: int = 1) -> dict:
        topic = await self._repo_get_topic(topic_id, tenant_id)
        if topic is None:
            raise NotFoundError("Topic not found")

        questions = await self._repo_list_questions_for_topic(topic_id, tenant_id)

        # Deterministic examples derived from topic metadata for MVP.
        examples: list[str] = []
        if topic.description:
            parts = [part.strip() for part in topic.description.split(".") if part.strip()]
            examples.extend(parts[:2])
        if not examples:
            examples = [f"Core example for {topic.name}", f"Applied example for {topic.name}"]

        return {
            "id": topic.id,
            "tenant_id": topic.tenant_id,
            "name": topic.name,
            "description": topic.description,
            "examples": examples,
            "practice_questions": [
                {
                    "id": question.id,
                    "difficulty": question.difficulty,
                    "question_type": getattr(question, "question_type", "short_text"),
                    "question_text": question.question_text,
                    "answer_options": list(getattr(question, "answer_options", []) or []),
                }
                for question in questions
            ],
        }

    async def explain_topic(self, *, tenant_id: int, topic_name: str) -> dict:
        data = await self.ai_service_client.explain_topic(topic_name=topic_name)
        guidance = data.get("guidance") or {}
        return {
            "topic_name": data.get("topic_name") or topic_name,
            "explanation": data.get("explanation") or "",
            "examples": data.get("examples", []),
            "use_cases": data.get("use_cases", []),
            "suggestions": guidance.get("suggestions", []),
            "next_steps": guidance.get("next_steps", []),
        }

    async def generate_ai_questions(
        self,
        *,
        tenant_id: int,
        topic: str,
        difficulty: str,
        count: int,
    ) -> dict:
        enabled = await self.feature_flag_service.is_enabled("ai_question_generation_enabled", tenant_id)
        if not enabled:
            raise ValidationError("AI question generation is disabled for this tenant")
        data = await self.ai_service_client.generate_questions(topic=topic, difficulty=difficulty, count=count)
        guidance = data.get("guidance") or {}
        return {
            "topic": data.get("topic") or topic,
            "difficulty": data.get("difficulty") or difficulty,
            "questions": data.get("questions", []),
            "suggestions": guidance.get("suggestions", []),
            "next_steps": guidance.get("next_steps", []),
        }

    async def create_topic(self, tenant_id: int = 1, name: str = "", description: str = ""):
        normalized_name = name.strip()
        if await self._repo_get_topic_by_name(tenant_id, normalized_name) is not None:
            raise ConflictError("Topic name already exists")
        try:
            topic = await self.repository.create_topic(
                tenant_id=tenant_id,
                name=normalized_name,
                description=description.strip(),
            )
        except TypeError:
            topic = await self.repository.create_topic(
                name=normalized_name,
                description=description.strip(),
            )
        await self.repository.session.commit()
        return topic

    async def update_topic(self, topic_id: int, tenant_id: int = 1, *, name: str | None = None, description: str | None = None):
        topic = await self._repo_get_topic(topic_id, tenant_id)
        if topic is None:
            raise NotFoundError("Topic not found")

        updates: dict[str, str] = {}
        if name is not None:
            normalized_name = name.strip()
            existing = await self._repo_get_topic_by_name(tenant_id, normalized_name)
            if existing is not None and existing.id != topic_id:
                raise ConflictError("Topic name already exists")
            updates["name"] = normalized_name
        if description is not None:
            updates["description"] = description.strip()

        updated = await self.repository.update_topic(topic, **updates)
        await self.repository.session.commit()
        return updated

    async def delete_topic(self, topic_id: int, tenant_id: int = 1) -> None:
        topic = await self._repo_get_topic(topic_id, tenant_id)
        if topic is None:
            raise NotFoundError("Topic not found")
        if await self._repo_list_questions_for_topic(topic_id, tenant_id):
            raise ValidationError("Cannot delete a topic that still has questions")
        await self.repository.delete_topic(topic)
        await self.repository.session.commit()

    async def list_prerequisites_page(self, limit: int, offset: int, tenant_id: int = 1, topic_id: int | None = None) -> dict:
        try:
            items = await self.repository.list_prerequisite_links(limit=limit, offset=offset, topic_id=topic_id, tenant_id=tenant_id)
            total = await self.repository.count_prerequisite_links(topic_id=topic_id, tenant_id=tenant_id)
        except TypeError:
            items = await self.repository.list_prerequisite_links(limit=limit, offset=offset, topic_id=topic_id)
            total = await self.repository.count_prerequisite_links(topic_id=topic_id)
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def create_prerequisite(self, topic_id: int, prerequisite_topic_id: int, tenant_id: int = 1):
        if topic_id == prerequisite_topic_id:
            raise ValidationError("A topic cannot depend on itself")

        topic = await self._repo_get_topic(topic_id, tenant_id)
        prerequisite = await self._repo_get_topic(prerequisite_topic_id, tenant_id)
        if topic is None or prerequisite is None:
            raise NotFoundError("Topic not found")

        try:
            prerequisite_link = await self.repository.get_prerequisite_link(topic_id, prerequisite_topic_id, tenant_id=tenant_id)
        except TypeError:
            prerequisite_link = await self.repository.get_prerequisite_link(topic_id, prerequisite_topic_id)
        if prerequisite_link is not None:
            raise ConflictError("Prerequisite link already exists")

        # Prevent cycles by ensuring the prerequisite does not already depend on the topic.
        graph_edges = await self.repository.get_prerequisite_edges(tenant_id=tenant_id)
        graph: dict[int, set[int]] = {}
        for child_id, parent_id in graph_edges:
            graph.setdefault(child_id, set()).add(parent_id)

        stack = [prerequisite_topic_id]
        visited: set[int] = set()
        while stack:
            current = stack.pop()
            if current == topic_id:
                raise ValidationError("Prerequisite link would create a cycle")
            if current in visited:
                continue
            visited.add(current)
            stack.extend(sorted(graph.get(current, set())))

        link = await self.repository.create_prerequisite_link(topic_id, prerequisite_topic_id)
        await self.repository.session.commit()
        return link

    async def delete_prerequisite(self, prerequisite_id: int, tenant_id: int = 1) -> None:
        try:
            link = await self.repository.get_prerequisite_link_by_id(prerequisite_id, tenant_id=tenant_id)
        except TypeError:
            link = await self.repository.get_prerequisite_link_by_id(prerequisite_id)
        if link is None:
            raise NotFoundError("Prerequisite link not found")
        await self.repository.delete_prerequisite_link(link)
        await self.repository.session.commit()

    async def list_questions_page(
        self,
        limit: int,
        offset: int,
        tenant_id: int = 1,
        topic_id: int | None = None,
        question_type: str | None = None,
        search: str | None = None,
    ) -> dict:
        items = await self._repo_list_questions(
            limit=limit,
            offset=offset,
            tenant_id=tenant_id,
            topic_id=topic_id,
            question_type=question_type,
            search=search,
        )
        total = await self._repo_count_questions(
            tenant_id=tenant_id,
            topic_id=topic_id,
            question_type=question_type,
            search=search,
        )
        next_offset = offset + limit if (offset + limit) < total else None
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "next_offset": next_offset,
                "next_cursor": None,
            },
        }

    async def create_question(
        self,
        topic_id: int,
        difficulty: int,
        question_type: str,
        question_text: str,
        correct_answer: str,
        accepted_answers: list[str],
        answer_options: list[str],
        tenant_id: int = 1,
    ):
        topic = await self._repo_get_topic(topic_id, tenant_id)
        if topic is None:
            raise NotFoundError("Topic not found")
        try:
            question = await self.repository.create_question(
                topic_id=topic_id,
                difficulty=difficulty,
                question_type=question_type,
                question_text=question_text,
                correct_answer=correct_answer,
                accepted_answers=accepted_answers,
                answer_options=answer_options,
            )
            await self.repository.session.commit()
            return question
        except ValueError as exc:
            await self.repository.session.rollback()
            raise ValidationError(str(exc)) from exc
        except Exception:
            await self.repository.session.rollback()
            raise

    async def update_question(self, question_id: int, **updates):
        question = await self.repository.get_question(question_id)
        if question is None:
            raise NotFoundError("Question not found")
        try:
            updated = await self.repository.update_question(
                question,
                **{key: value for key, value in updates.items() if value is not None},
            )
            await self.repository.session.commit()
            return updated
        except ValueError as exc:
            await self.repository.session.rollback()
            raise ValidationError(str(exc)) from exc
        except Exception:
            await self.repository.session.rollback()
            raise

    async def delete_question(self, question_id: int) -> None:
        question = await self.repository.get_question(question_id)
        if question is None:
            raise NotFoundError("Question not found")
        await self.repository.delete_question(question)
        await self.repository.session.commit()

    async def import_questions(self, items: list[dict], tenant_id: int = 1) -> int:
        created = 0
        try:
            for item in items:
                topic = await self._repo_get_topic(item["topic_id"], tenant_id)
                if topic is None:
                    raise NotFoundError(f"Topic {item['topic_id']} not found")
                await self.repository.create_question(**item)
                created += 1
            await self.repository.session.commit()
            return created
        except ValueError as exc:
            await self.repository.session.rollback()
            raise ValidationError(str(exc)) from exc
        except Exception:
            await self.repository.session.rollback()
            raise

    async def import_questions_csv(self, content: str, tenant_id: int = 1) -> int:
        try:
            reader = csv.DictReader(io.StringIO(content))
            items: list[dict] = []
            for row in reader:
                items.append(
                    {
                        "topic_id": int((row.get("topic_id") or "").strip()),
                        "difficulty": int((row.get("difficulty") or "").strip()),
                        "question_type": (row.get("question_type") or "short_text").strip(),
                        "question_text": (row.get("question_text") or "").strip(),
                        "correct_answer": (row.get("correct_answer") or "").strip(),
                        "accepted_answers": [
                            item.strip()
                            for item in (row.get("accepted_answers") or "").split("|")
                            if item.strip()
                        ],
                        "answer_options": [
                            item.strip()
                            for item in (row.get("answer_options") or "").split("|")
                            if item.strip()
                        ],
                    }
                )
        except (TypeError, ValueError) as exc:
            raise ValidationError("Invalid CSV import payload") from exc

        if not items:
            raise ValidationError("CSV import must contain at least one question")

        return await self.import_questions(items, tenant_id=tenant_id)

    async def export_questions(self, tenant_id: int = 1, topic_id: int | None = None) -> list[dict]:
        items = await self._repo_list_questions(
            limit=10_000,
            offset=0,
            tenant_id=tenant_id,
            topic_id=topic_id,
            question_type=None,
            search=None,
        )
        return [
            {
                "id": question.id,
                "topic_id": question.topic_id,
                "difficulty": question.difficulty,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "correct_answer": question.correct_answer,
                "accepted_answers": list(question.accepted_answers),
                "answer_options": list(question.answer_options),
            }
            for question in items
        ]

    async def export_questions_csv(self, tenant_id: int = 1, topic_id: int | None = None) -> str:
        items = await self.export_questions(tenant_id=tenant_id, topic_id=topic_id)
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "topic_id",
                "difficulty",
                "question_type",
                "question_text",
                "correct_answer",
                "accepted_answers",
                "answer_options",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    **item,
                    "accepted_answers": "|".join(item["accepted_answers"]),
                    "answer_options": "|".join(item["answer_options"]),
                }
            )
        return output.getvalue()
