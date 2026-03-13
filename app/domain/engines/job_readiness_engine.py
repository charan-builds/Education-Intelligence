from __future__ import annotations


class JobReadinessEngine:
    """
    Computes a job-readiness score in range [0, 100].

    Inputs:
    - user_skills: list[dict] with at least average_score (0-100) per skill
    - completed_roadmap: dict with either completion_rate (0-100) or step stats
    - topic_mastery: dict[topic_id, score] where score is 0-100

    Score composition:
    - skill_coverage: 40%
    - topic_mastery: 35%
    - practice_completion: 25%
    """

    SKILL_WEIGHT = 0.40
    TOPIC_WEIGHT = 0.35
    PRACTICE_WEIGHT = 0.25

    def compute_score(
        self,
        user_skills: list[dict],
        completed_roadmap: dict,
        topic_mastery: dict[int, float],
    ) -> dict:
        skill_coverage = self._compute_skill_coverage(user_skills)
        topic_mastery_score = self._compute_topic_mastery(topic_mastery)
        practice_completion = self._compute_practice_completion(completed_roadmap)

        weighted = (
            (skill_coverage * self.SKILL_WEIGHT)
            + (topic_mastery_score * self.TOPIC_WEIGHT)
            + (practice_completion * self.PRACTICE_WEIGHT)
        )
        readiness_score = round(max(0.0, min(100.0, weighted)), 2)

        return {
            "job_readiness_score": readiness_score,
            "breakdown": {
                "skill_coverage": round(skill_coverage, 2),
                "topic_mastery": round(topic_mastery_score, 2),
                "practice_completion": round(practice_completion, 2),
            },
            "weights": {
                "skill_coverage": self.SKILL_WEIGHT,
                "topic_mastery": self.TOPIC_WEIGHT,
                "practice_completion": self.PRACTICE_WEIGHT,
            },
        }

    @staticmethod
    def _compute_skill_coverage(user_skills: list[dict]) -> float:
        if not user_skills:
            return 0.0
        scores: list[float] = []
        for skill in user_skills:
            value = float(skill.get("average_score", 0.0))
            scores.append(max(0.0, min(100.0, value)))
        return sum(scores) / len(scores)

    @staticmethod
    def _compute_topic_mastery(topic_mastery: dict[int, float]) -> float:
        if not topic_mastery:
            return 0.0
        values = [max(0.0, min(100.0, float(score))) for score in topic_mastery.values()]
        return sum(values) / len(values)

    @staticmethod
    def _compute_practice_completion(completed_roadmap: dict) -> float:
        if "completion_rate" in completed_roadmap:
            return max(0.0, min(100.0, float(completed_roadmap.get("completion_rate", 0.0))))

        completed_steps = int(completed_roadmap.get("completed_steps", 0))
        total_steps = int(completed_roadmap.get("total_steps", 0))
        if total_steps <= 0:
            return 0.0
        return max(0.0, min(100.0, (completed_steps / total_steps) * 100.0))
