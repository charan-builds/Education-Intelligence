from __future__ import annotations

from random import Random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.goal import Goal
from app.domain.models.goal_topic import GoalTopic
from app.domain.models.question import Question
from app.domain.models.topic import Topic
from app.domain.models.topic_prerequisite import TopicPrerequisite
from scripts.demo_data_factory import build_demo_personal_workspaces, build_goal_topic_names


class PersonalTenantProvisioningService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def provision_defaults(self, *, tenant_id: int) -> None:
        existing_goal = (
            await self.session.execute(select(Goal.id).where(Goal.tenant_id == tenant_id).limit(1))
        ).scalar_one_or_none()
        if existing_goal is not None:
            return

        catalog = self._build_catalog()
        topic_rows: dict[str, Topic] = {}

        for topic_spec in catalog["topics"]:
            topic = (
                await self.session.execute(select(Topic).where(Topic.tenant_id == tenant_id, Topic.name == topic_spec["name"]))
            ).scalar_one_or_none()
            if topic is None:
                topic = Topic(
                    tenant_id=tenant_id,
                    name=topic_spec["name"],
                    description=topic_spec["description"],
                )
                self.session.add(topic)
                await self.session.flush()
            topic_rows[topic.name] = topic

            for question_spec in topic_spec["questions"]:
                question = (
                    await self.session.execute(
                        select(Question).where(
                            Question.topic_id == topic.id,
                            Question.question_text == question_spec["question_text"],
                        )
                    )
                ).scalar_one_or_none()
                if question is None:
                    self.session.add(
                        Question(
                            topic_id=topic.id,
                            difficulty=question_spec["difficulty"],
                            question_type=question_spec["question_type"],
                            question_text=question_spec["question_text"],
                            correct_answer=question_spec["correct_answer"],
                            accepted_answers=question_spec["accepted_answers"],
                            answer_options=question_spec["answer_options"],
                        )
                    )

        topic_names = list(topic_rows.keys())
        for index in range(1, len(topic_names)):
            topic = topic_rows[topic_names[index]]
            prerequisite = topic_rows[topic_names[index - 1]]
            existing_edge = (
                await self.session.execute(
                    select(TopicPrerequisite).where(
                        TopicPrerequisite.topic_id == topic.id,
                        TopicPrerequisite.prerequisite_topic_id == prerequisite.id,
                    )
                )
            ).scalar_one_or_none()
            if existing_edge is None:
                self.session.add(
                    TopicPrerequisite(topic_id=topic.id, prerequisite_topic_id=prerequisite.id)
                )

        topic_groups = build_goal_topic_names(topic_names, len(catalog["goals"]), rng=Random(f"personal-{tenant_id}-goals"))
        for goal_spec, selected_topics in zip(catalog["goals"], topic_groups, strict=False):
            goal = (
                await self.session.execute(select(Goal).where(Goal.tenant_id == tenant_id, Goal.name == goal_spec["name"]))
            ).scalar_one_or_none()
            if goal is None:
                goal = Goal(
                    tenant_id=tenant_id,
                    name=goal_spec["name"],
                    description=goal_spec["description"],
                    skills_covered=selected_topics[:4],
                    estimated_duration_weeks=goal_spec["estimated_duration_weeks"],
                    difficulty_tag=goal_spec["difficulty_tag"],
                    roadmap_preview=self._roadmap_preview(selected_topics),
                )
                self.session.add(goal)
                await self.session.flush()

            for topic_name in selected_topics:
                topic = topic_rows[topic_name]
                existing_link = (
                    await self.session.execute(
                        select(GoalTopic).where(GoalTopic.goal_id == goal.id, GoalTopic.topic_id == topic.id)
                    )
                ).scalar_one_or_none()
                if existing_link is None:
                    self.session.add(GoalTopic(goal_id=goal.id, topic_id=topic.id))

        await self.session.flush()

    @staticmethod
    def _roadmap_preview(selected_topics: list[str]) -> str:
        if not selected_topics:
            return "The roadmap begins with a lightweight diagnostic and adapts based on your strongest and weakest signals."
        opening = ", ".join(selected_topics[:3])
        return (
            f"Start with {opening}, then adapt the roadmap around your weakest concepts, prerequisite gaps, and diagnostic pace."
        )

    @staticmethod
    def _build_catalog() -> dict[str, list[dict]]:
        workspaces = build_demo_personal_workspaces()
        topics_by_name: dict[str, dict] = {}
        goals_by_name: dict[str, dict] = {}
        difficulty_cycle = ["beginner", "beginner", "intermediate", "intermediate", "advanced", "beginner"]
        duration_cycle = [4, 6, 8, 10, 12, 5]

        for workspace in workspaces:
            for topic in workspace.get("topics", []):
                topics_by_name.setdefault(topic["name"], topic)
            for goal in workspace.get("goals", []):
                goals_by_name.setdefault(goal["name"], goal)

        goal_rows: list[dict] = []
        for index, goal in enumerate(goals_by_name.values()):
            goal_rows.append(
                {
                    "name": goal["name"],
                    "description": goal["description"],
                    "difficulty_tag": difficulty_cycle[index % len(difficulty_cycle)],
                    "estimated_duration_weeks": duration_cycle[index % len(duration_cycle)],
                }
            )

        return {
            "topics": list(topics_by_name.values()),
            "goals": goal_rows,
        }
