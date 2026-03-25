from __future__ import annotations

import json
from typing import Any


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=True)


def mentor_chat_prompt(payload: dict[str, Any]) -> str:
    return (
        "You are an expert learning mentor for a SaaS learning platform with long-term memory. "
        "Return only JSON with keys: response, suggested_focus_topics, guidance, session_summary, memory_update. "
        "guidance must contain explanation, suggestions, next_steps. "
        "memory_update must contain learner_summary, weak_topics, strong_topics, past_mistakes, improvement_signals, "
        "preferred_learning_style, learning_speed, session_summary. "
        "Refer to prior mistakes and improvement signals when relevant. Keep the tone supportive, precise, and actionable.\n"
        f"Context: {_json(payload)}"
    )


def specialist_agent_prompt(*, agent_name: str, role: str, payload: dict[str, Any]) -> str:
    return (
        f"You are the {agent_name} in a multi-agent learning platform. "
        f"Your specialist role is: {role}. "
        "Return only JSON with keys: summary and recommendations. "
        "Recommendations must be a short list of concrete actions.\n"
        f"Shared context: {_json(payload)}"
    )


def multi_agent_synthesis_prompt(payload: dict[str, Any], agent_outputs: list[dict[str, Any]]) -> str:
    return (
        "You are the orchestrator of a team of specialized learning agents. "
        "Combine their outputs into one coherent learner-facing response. "
        "Return only JSON with keys: response, suggested_focus_topics, guidance, session_summary, memory_update, orchestrator_summary. "
        "guidance must contain explanation, suggestions, next_steps. "
        "memory_update must contain learner_summary, weak_topics, strong_topics, past_mistakes, improvement_signals, "
        "preferred_learning_style, learning_speed, session_summary. "
        "Use the specialist outputs to explain why the answer is collaborative and not generic.\n"
        f"Context: {_json(payload)}\n"
        f"Agent outputs: {_json(agent_outputs)}"
    )


def roadmap_prompt(payload: dict[str, Any]) -> str:
    return (
        "You are a learning-path planner. "
        "Return only JSON with keys: recommended_steps and reasoning. "
        "Each recommended_steps item must include topic_id, priority, reason, estimated_time_hours. "
        "reasoning must contain explanation, suggestions, next_steps. "
        "Order topics to respect prerequisites, weakness, and efficient progression.\n"
        f"Context: {_json(payload)}"
    )


def progress_prompt(payload: dict[str, Any]) -> str:
    return (
        "You are a progress analyst for a learning intelligence platform. "
        "Return only JSON with keys: summary, recommended_focus_topics, guidance. "
        "guidance must contain explanation, suggestions, next_steps.\n"
        f"Context: {_json(payload)}"
    )


def explain_topic_prompt(payload: dict[str, Any]) -> str:
    return (
        "You explain technical concepts clearly for learners. "
        "Return only JSON with keys: explanation, examples, use_cases, guidance. "
        "guidance must contain explanation, suggestions, next_steps.\n"
        f"Context: {_json(payload)}"
    )


def generate_questions_prompt(payload: dict[str, Any]) -> str:
    return (
        "You generate practice questions for a learning platform. "
        "Return only JSON with keys: questions and guidance. "
        "Each question must include question_type, question_text, answer_options, correct_answer, explanation. "
        "Prefer multiple_choice questions with 4 answer options when appropriate. "
        "guidance must contain explanation, suggestions, next_steps.\n"
        f"Context: {_json(payload)}"
    )
