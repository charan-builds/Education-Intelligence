import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.domain.models import Goal, Question, Tenant, Topic, TopicPrerequisite, User
from app.domain.models.tenant import TenantType
from app.domain.models.user import UserRole
from app.infrastructure.database import AsyncSessionLocal


def _utcnow():
    return datetime.now(timezone.utc)


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.name == "Platform"))
        ).scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name="Platform", type=TenantType.platform, created_at=_utcnow())
            session.add(tenant)
            await session.flush()

        super_admin = (
            await session.execute(select(User).where(User.email == "admin@platform.local"))
        ).scalar_one_or_none()
        if super_admin is None:
            session.add(
                User(
                    tenant_id=tenant.id,
                    email="admin@platform.local",
                    password_hash=hash_password("ChangeMe123!"),
                    role=UserRole.super_admin,
                    created_at=_utcnow(),
                )
            )

        goals = [
            ("AI/ML Engineer", "Build ML systems and deploy intelligent pipelines."),
            ("Web Developer", "Design and build modern full-stack web applications."),
            ("Data Analyst", "Analyze data for reporting, insights, and decisions."),
            ("Video Editor", "Produce high quality edited video content."),
        ]
        for name, description in goals:
            exists = (await session.execute(select(Goal).where(Goal.name == name))).scalar_one_or_none()
            if exists is None:
                session.add(Goal(name=name, description=description))

        topics = {
            "Linear Algebra": "Vector spaces, matrices, and transformations.",
            "Statistics": "Probability, distributions, and inference.",
            "Machine Learning": "Supervised and unsupervised model fundamentals.",
        }
        topic_rows: dict[str, Topic] = {}
        for name, description in topics.items():
            row = (await session.execute(select(Topic).where(Topic.name == name))).scalar_one_or_none()
            if row is None:
                row = Topic(name=name, description=description)
                session.add(row)
                await session.flush()
            topic_rows[name] = row

        prereq_edges = [
            ("Statistics", "Linear Algebra"),
            ("Machine Learning", "Statistics"),
        ]
        for topic_name, prereq_name in prereq_edges:
            topic_id = topic_rows[topic_name].id
            prereq_id = topic_rows[prereq_name].id
            exists = (
                await session.execute(
                    select(TopicPrerequisite).where(
                        TopicPrerequisite.topic_id == topic_id,
                        TopicPrerequisite.prerequisite_topic_id == prereq_id,
                    )
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(TopicPrerequisite(topic_id=topic_id, prerequisite_topic_id=prereq_id))

        question_templates = [
            ("Linear Algebra", 1, "What is a vector space?"),
            ("Statistics", 2, "Explain standard deviation and variance."),
            ("Machine Learning", 3, "Differentiate overfitting and underfitting."),
        ]
        for topic_name, difficulty, text in question_templates:
            topic_id = topic_rows[topic_name].id
            exists = (
                await session.execute(
                    select(Question).where(Question.topic_id == topic_id, Question.question_text == text)
                )
            ).scalar_one_or_none()
            if exists is None:
                session.add(Question(topic_id=topic_id, difficulty=difficulty, question_text=text))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
    print("Seed bootstrap complete")
