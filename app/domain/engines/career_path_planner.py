from __future__ import annotations


class CareerPathPlanner:
    """
    Generates a long-term career roadmap with three phases:
    1) foundations
    2) intermediate_skills
    3) advanced_specialization
    """

    _DEFAULT_FOUNDATIONS = [
        "Core fundamentals",
        "Tooling and workflow basics",
        "Problem-solving patterns",
    ]
    _DEFAULT_INTERMEDIATE = [
        "Applied projects",
        "System design and architecture",
        "Testing and reliability practices",
    ]
    _DEFAULT_ADVANCED = [
        "Specialization track",
        "Portfolio capstone",
        "Interview and real-world readiness",
    ]

    _PROFILE_MONTH_MULTIPLIER = {
        "practice_focused": 0.9,
        "balanced": 1.0,
        "concept_focused": 1.1,
        "slow_deep_learner": 1.25,
    }

    _SKILL_LEVEL_BASE_MONTHS = {
        "beginner": 12,
        "intermediate": 8,
        "advanced": 5,
    }

    def generate_path(
        self,
        goal: dict,
        current_skill_level: str,
        learning_profile: dict,
    ) -> dict:
        goal_name = str(goal.get("name", "Career Goal"))
        profile_type = str(learning_profile.get("profile_type", "balanced"))

        base_months = self._SKILL_LEVEL_BASE_MONTHS.get(current_skill_level, 10)
        multiplier = self._PROFILE_MONTH_MULTIPLIER.get(profile_type, 1.0)
        total_months = max(3, int(round(base_months * multiplier)))

        foundations_months = max(1, int(round(total_months * 0.4)))
        intermediate_months = max(1, int(round(total_months * 0.35)))
        advanced_months = max(1, total_months - foundations_months - intermediate_months)

        foundations_topics = goal.get("foundations") or self._DEFAULT_FOUNDATIONS
        intermediate_topics = goal.get("intermediate") or self._DEFAULT_INTERMEDIATE
        advanced_topics = goal.get("advanced") or self._DEFAULT_ADVANCED

        return {
            "goal": goal_name,
            "current_skill_level": current_skill_level,
            "learning_profile": profile_type,
            "estimated_duration_months": total_months,
            "career_roadmap": {
                "phase_1_foundations": {
                    "duration_months": foundations_months,
                    "focus_areas": list(foundations_topics),
                },
                "phase_2_intermediate_skills": {
                    "duration_months": intermediate_months,
                    "focus_areas": list(intermediate_topics),
                },
                "phase_3_advanced_specialization": {
                    "duration_months": advanced_months,
                    "focus_areas": list(advanced_topics),
                },
            },
        }
