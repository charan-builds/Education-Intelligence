from app.domain.engines.career_path_planner import CareerPathPlanner


def test_career_path_contains_three_phases():
    planner = CareerPathPlanner()
    roadmap = planner.generate_path(
        goal={"name": "ML Engineer"},
        current_skill_level="beginner",
        learning_profile={"profile_type": "balanced"},
    )

    phases = roadmap["career_roadmap"]
    assert "phase_1_foundations" in phases
    assert "phase_2_intermediate_skills" in phases
    assert "phase_3_advanced_specialization" in phases


def test_profile_changes_estimated_duration():
    planner = CareerPathPlanner()

    fast = planner.generate_path(
        goal={"name": "Data Analyst"},
        current_skill_level="intermediate",
        learning_profile={"profile_type": "practice_focused"},
    )
    slow = planner.generate_path(
        goal={"name": "Data Analyst"},
        current_skill_level="intermediate",
        learning_profile={"profile_type": "slow_deep_learner"},
    )

    assert slow["estimated_duration_months"] > fast["estimated_duration_months"]


def test_goal_specific_focus_areas_override_defaults():
    planner = CareerPathPlanner()
    roadmap = planner.generate_path(
        goal={
            "name": "Web Developer",
            "foundations": ["HTML/CSS", "JavaScript basics"],
            "intermediate": ["Backend APIs", "Database design"],
            "advanced": ["Scalability", "Security hardening"],
        },
        current_skill_level="beginner",
        learning_profile={"profile_type": "concept_focused"},
    )

    assert roadmap["career_roadmap"]["phase_1_foundations"]["focus_areas"] == ["HTML/CSS", "JavaScript basics"]
    assert roadmap["career_roadmap"]["phase_3_advanced_specialization"]["focus_areas"] == ["Scalability", "Security hardening"]
