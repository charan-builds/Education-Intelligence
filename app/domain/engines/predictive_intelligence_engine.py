from __future__ import annotations


class PredictiveIntelligenceEngine:
    def predict_failure_risk(
        self,
        *,
        completion_percent: float,
        average_score: float,
        consistency_score: float,
        retention_score: float,
        weak_topic_count: int,
        overdue_steps: int,
    ) -> dict:
        risk_score = (
            (100.0 - completion_percent) * 0.26
            + (100.0 - average_score) * 0.24
            + (100.0 - consistency_score) * 0.18
            + (100.0 - retention_score) * 0.14
            + (weak_topic_count * 4.5)
            + (overdue_steps * 5.0)
        )
        risk_score = round(max(0.0, min(100.0, risk_score)), 2)
        if risk_score >= 68:
            level = "high"
        elif risk_score >= 42:
            level = "medium"
        else:
            level = "low"

        interventions: list[str] = []
        if weak_topic_count:
            interventions.append("Prioritize one weak concept cluster before new advanced work.")
        if overdue_steps:
            interventions.append("Reduce plan load and complete one overdue roadmap item this week.")
        if retention_score < 65:
            interventions.append("Inject a spaced revision block within the next 48 hours.")
        if consistency_score < 60:
            interventions.append("Use shorter daily sessions to rebuild study consistency.")
        if not interventions:
            interventions.append("Maintain current pace and keep one revision slot per week.")

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "recommended_interventions": interventions[:4],
        }
