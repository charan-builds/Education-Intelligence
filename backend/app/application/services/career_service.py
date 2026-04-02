from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.ai_request_service import AIRequestService
from app.domain.engines.career_path_planner import CareerPathPlanner
from app.domain.engines.job_readiness_engine import JobReadinessEngine
from app.domain.engines.skill_graph_engine import SkillGraphEngine
from app.domain.models.badge import Badge
from app.domain.models.job_role import JobRole
from app.domain.models.job_role_skill import JobRoleSkill
from app.domain.models.learning_event import LearningEvent
from app.domain.models.skill import Skill
from app.domain.models.topic_score import TopicScore
from app.domain.models.user import User
from app.infrastructure.repositories.roadmap_repository import RoadmapRepository


class CareerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.roadmap_repository = RoadmapRepository(session)
        self.skill_graph_engine = SkillGraphEngine(session, tenant_id=1)
        self.job_readiness_engine = JobReadinessEngine()
        self.career_path_planner = CareerPathPlanner()
        self.ai_request_service = AIRequestService(session)

    async def _skill_progress(self, *, user_id: int, tenant_id: int) -> dict:
        self.skill_graph_engine.tenant_id = tenant_id
        return await self.skill_graph_engine.compute_skill_progress(user_id)

    async def _topic_scores(self, *, user_id: int, tenant_id: int) -> dict[int, float]:
        result = await self.session.execute(
            select(TopicScore.topic_id, TopicScore.score).where(TopicScore.user_id == user_id, TopicScore.tenant_id == tenant_id)
        )
        return {int(topic_id): float(score) for topic_id, score in result.all()}

    async def _roadmap_progress(self, *, user_id: int, tenant_id: int) -> dict:
        roadmap = await self.roadmap_repository.get_latest_roadmap_for_user(user_id=user_id, tenant_id=tenant_id)
        steps = roadmap.steps if roadmap is not None else []
        completed = sum(1 for step in steps if str(step.progress_status).lower() == "completed")
        total = len(steps)
        completion_rate = round((completed / total) * 100.0, 2) if total else 0.0
        return {
            "completed_steps": completed,
            "total_steps": total,
            "completion_rate": completion_rate,
        }

    async def _role_matches(self, *, tenant_id: int, user_skills: list[dict]) -> list[dict]:
        role_rows = await self.session.execute(
            select(JobRole.id, JobRole.name, JobRole.category, Skill.name)
            .join(JobRoleSkill, JobRoleSkill.job_role_id == JobRole.id)
            .join(Skill, Skill.id == JobRoleSkill.skill_id)
            .where(JobRole.tenant_id == tenant_id)
            .order_by(JobRole.id.asc())
        )
        skills_by_role: dict[int, dict] = {}
        user_skill_names = {str(skill["skill_name"]).lower(): float(skill["average_score"]) for skill in user_skills}

        for role_id, role_name, category, skill_name in role_rows.all():
            bucket = skills_by_role.setdefault(
                int(role_id),
                {"role_id": int(role_id), "role_name": str(role_name), "category": str(category), "skills": []},
            )
            bucket["skills"].append(str(skill_name))

        matches: list[dict] = []
        for role in skills_by_role.values():
            required = role["skills"]
            matched = [skill for skill in required if skill.lower() in user_skill_names]
            missing = [skill for skill in required if skill.lower() not in user_skill_names]
            if required:
                skill_score = sum(user_skill_names.get(skill.lower(), 0.0) for skill in required) / len(required)
            else:
                skill_score = 0.0
            matches.append(
                {
                    "role_id": role["role_id"],
                    "role_name": role["role_name"],
                    "category": role["category"],
                    "readiness_percent": round(skill_score, 2),
                    "matched_skills": matched[:6],
                    "missing_skills": missing[:6],
                }
            )
        matches.sort(key=lambda item: item["readiness_percent"], reverse=True)
        return matches

    async def get_job_readiness(self, *, user_id: int, tenant_id: int) -> dict:
        user_skill_progress = await self._skill_progress(user_id=user_id, tenant_id=tenant_id)
        topic_scores = await self._topic_scores(user_id=user_id, tenant_id=tenant_id)
        roadmap_progress = await self._roadmap_progress(user_id=user_id, tenant_id=tenant_id)

        readiness = self.job_readiness_engine.compute_score(
            user_skills=user_skill_progress["skills"],
            completed_roadmap=roadmap_progress,
            topic_mastery=topic_scores,
        )
        role_matches = await self._role_matches(tenant_id=tenant_id, user_skills=user_skill_progress["skills"])
        score = float(readiness["job_readiness_score"])
        confidence_label = "early"
        if score >= 75:
            confidence_label = "high"
        elif score >= 55:
            confidence_label = "medium"

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "readiness_percent": score,
            "confidence_label": confidence_label,
            "breakdown": readiness["breakdown"],
            "top_role_matches": role_matches[:3],
            "alternative_paths": role_matches[3:6],
        }

    async def get_resume_preview(self, *, user_id: int, tenant_id: int) -> dict:
        user = await self.session.get(User, user_id)
        skill_progress = await self._skill_progress(user_id=user_id, tenant_id=tenant_id)
        badges_result = await self.session.execute(
            select(Badge.name).where(Badge.user_id == user_id, Badge.tenant_id == tenant_id).order_by(Badge.awarded_at.desc()).limit(4)
        )
        badges = [str(name) for name in badges_result.scalars().all()]
        events_result = await self.session.execute(
            select(LearningEvent.event_type, LearningEvent.topic_id)
            .where(LearningEvent.user_id == user_id, LearningEvent.tenant_id == tenant_id)
            .order_by(LearningEvent.created_at.desc())
            .limit(6)
        )
        projects = [f"{event_type.replace('_', ' ').title()} for topic {topic_id}" for event_type, topic_id in events_result.all() if topic_id]
        mastered_skills = [item["skill_name"] for item in skill_progress["skills"] if item["level"] == "mastered"]

        display_name = user.display_name if user is not None and user.display_name else "Learner"
        return {
            "headline": f"{display_name} • Emerging {mastered_skills[0] if mastered_skills else 'Technical'} Talent",
            "summary": (
                f"Adaptive learner with {round(skill_progress['overall_progress'], 1)}% average skill progress, "
                f"strong momentum across guided roadmap work, and practice-backed topic mastery."
            ),
            "skills": mastered_skills[:8],
            "projects": projects[:4],
            "achievements": badges[:4],
        }

    async def get_career_path(self, *, user_id: int, tenant_id: int) -> dict:
        readiness = await self.get_job_readiness(user_id=user_id, tenant_id=tenant_id)
        top_role = readiness["top_role_matches"][0] if readiness["top_role_matches"] else {"role_name": "Career Role"}
        skill_progress = await self._skill_progress(user_id=user_id, tenant_id=tenant_id)
        overall = float(skill_progress["overall_progress"])
        current_skill_level = "beginner" if overall < 50 else "intermediate" if overall < 75 else "advanced"
        return self.career_path_planner.generate_path(
            goal={"name": top_role["role_name"]},
            current_skill_level=current_skill_level,
            learning_profile={"profile_type": "practice_focused" if readiness["breakdown"]["practice_completion"] >= 60 else "balanced"},
        )

    async def get_interview_prep(self, *, user_id: int, tenant_id: int, role_name: str, difficulty: str, count: int) -> dict:
        queued = await self.ai_request_service.queue_career_interview_prep(
            tenant_id=tenant_id,
            user_id=user_id,
            role_name=role_name,
            difficulty=difficulty,
            count=count,
        )
        resolved = await self.ai_request_service.get_result(
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=str(queued["request_id"]),
        )
        questions = (resolved or {}).get("result") or AIRequestService._fallback_result(
            request_type=AIRequestService.TYPE_CAREER_INTERVIEW_PREP,
            payload={"role_name": role_name, "difficulty": difficulty, "count": count},
        )
        skill_progress = await self._skill_progress(user_id=user_id, tenant_id=tenant_id)
        return {
            "role_name": role_name,
            "mock_interview_prompt": (
                f"Act as a hiring manager for a {role_name} role. Ask targeted questions, score each answer, "
                f"and adapt based on the learner's strongest skills: {', '.join(item['skill_name'] for item in skill_progress['skills'][:3])}."
            ),
            "questions": questions.get("questions", []),
        }

    async def get_overview(self, *, user_id: int, tenant_id: int) -> dict:
        readiness = await self.get_job_readiness(user_id=user_id, tenant_id=tenant_id)
        return {
            "readiness": readiness,
            "resume_preview": await self.get_resume_preview(user_id=user_id, tenant_id=tenant_id),
            "career_path": await self.get_career_path(user_id=user_id, tenant_id=tenant_id),
        }
